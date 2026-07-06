"""Home Utility Health Report engine.

Judges the *home*, not the latest bill: retrospective anomaly timeline,
consumption-floor leak detection, base-load estimation, and tariff-slab
positioning over the full bill history. Same doctrine as `analysis.py`:
dependency-light, ORM-free, deterministic — every figure is auditable and the
LLM layer only phrases them.

Electricity excess is priced exactly via the slab tariff engine
(cost(actual) - cost(baseline)); water uses the period's own unit rate.
"""

import statistics
from dataclasses import dataclass
from datetime import date

from app.models.bill import UtilityType
from app.schemas.analysis import (
    ConsumptionStatus,
    Effort,
    Recommendation,
    RecommendationCategory,
)
from app.schemas.report import (
    BaseLoadEstimate,
    FloorRiseAssessment,
    HealthReport,
    SlabPosition,
    TimelineEntry,
)
from app.services.analysis import DEFAULT_UNITS
from app.services.tariff import electricity_cost, electricity_marginal_rate, next_slab_gap

MIN_PERIODS = 6
BASE_LOAD_MIN_PERIODS = 12  # a full seasonal cycle
FLOOR_WINDOW = 6
FLOOR_MIN_PRIOR = 3
WARNING_Z = 1.0


@dataclass(frozen=True)
class DatedBillPoint:
    period_start: date
    period_end: date
    consumption: float
    cost: float


def _unit_rate(point: DatedBillPoint) -> float:
    return point.cost / point.consumption if point.consumption > 0 else 0.0


def _excess_cost(utility_type: UtilityType, point: DatedBillPoint, baseline_mean: float) -> float:
    if point.consumption <= baseline_mean:
        return 0.0
    if utility_type == UtilityType.electricity:
        y, m = point.period_start.year, point.period_start.month
        return electricity_cost(point.consumption, year=y, month=m) - electricity_cost(
            baseline_mean, year=y, month=m
        )
    return (point.consumption - baseline_mean) * _unit_rate(point)


def _status(consumption: float, mean: float, stdev: float, z_threshold: float) -> ConsumptionStatus:
    if stdev > 0:
        z = (consumption - mean) / stdev
        if z >= z_threshold:
            return ConsumptionStatus.anomaly
        if z >= WARNING_Z:
            return ConsumptionStatus.warning
        return ConsumptionStatus.normal
    ratio = consumption / mean if mean > 0 else 1.0
    if ratio >= 1.5:
        return ConsumptionStatus.anomaly
    if ratio >= 1.2:
        return ConsumptionStatus.warning
    return ConsumptionStatus.normal


def _timeline(
    utility_type: UtilityType, points: list[DatedBillPoint], z_threshold: float
) -> list[TimelineEntry]:
    entries = []
    for i in range(2, len(points)):
        priors = [p.consumption for p in points[:i]]
        mean = statistics.fmean(priors)
        stdev = statistics.stdev(priors) if len(priors) >= 2 else 0.0
        status = _status(points[i].consumption, mean, stdev, z_threshold)
        excess = (
            _excess_cost(utility_type, points[i], mean)
            if status in (ConsumptionStatus.warning, ConsumptionStatus.anomaly)
            else 0.0
        )
        entries.append(
            TimelineEntry(
                period_start=points[i].period_start,
                period_end=points[i].period_end,
                consumption=points[i].consumption,
                status=status,
                excess_cost=round(excess, 2),
            )
        )
    return entries


def _floor_rise(points: list[DatedBillPoint], ratio_threshold: float) -> FloorRiseAssessment:
    recent = points[-FLOOR_WINDOW:]
    prior = points[:-FLOOR_WINDOW]
    recent_floor = min(p.consumption for p in recent)
    if len(prior) < FLOOR_MIN_PRIOR:
        return FloorRiseAssessment(
            suspected=False,
            recent_floor=round(recent_floor, 2),
            prior_floor=round(recent_floor, 2),
            ratio=None,
            reason="Not enough history to compare your consumption floor over time yet.",
        )
    prior_floor = min(p.consumption for p in prior)
    ratio = recent_floor / prior_floor if prior_floor > 0 else None
    suspected = ratio is not None and ratio >= ratio_threshold
    if suspected:
        reason = (
            f"Your lowest month is now {round((ratio - 1) * 100)}% above what it used to be — "
            "something is consuming continuously, even in your quietest months."
        )
    else:
        reason = "Your consumption floor is stable — no sign of a continuous leak or load."
    return FloorRiseAssessment(
        suspected=suspected,
        recent_floor=round(recent_floor, 2),
        prior_floor=round(prior_floor, 2),
        ratio=round(ratio, 2) if ratio is not None else None,
        reason=reason,
    )


def _base_load(points: list[DatedBillPoint]) -> BaseLoadEstimate | None:
    if len(points) < BASE_LOAD_MIN_PERIODS:
        return None
    lowest = sorted(p.consumption for p in points)[:3]
    base = statistics.fmean(lowest)
    total = sum(p.consumption for p in points)
    latest = points[-1]
    monthly_cost = electricity_cost(base, year=latest.period_start.year, month=latest.period_start.month)
    return BaseLoadEstimate(
        monthly_consumption=round(base, 2),
        monthly_cost=round(monthly_cost, 2),
        share_of_total=round(base * len(points) / total, 2) if total > 0 else 0.0,
    )


def _recommendations(
    utility_type: UtilityType,
    points: list[DatedBillPoint],
    floor: FloorRiseAssessment,
    base_load: BaseLoadEstimate | None,
    slab: SlabPosition | None,
    currency: str,
) -> list[Recommendation]:
    recs: list[Recommendation] = []
    latest = points[-1]

    if floor.suspected:
        annualized = (floor.recent_floor - floor.prior_floor) * _unit_rate(latest) * 12
        recs.append(
            Recommendation(
                title=(
                    "Find the continuous water flow"
                    if utility_type == UtilityType.water
                    else "Find the always-on electrical load"
                ),
                category=RecommendationCategory.maintenance,
                reason=floor.reason,
                estimated_savings=round(annualized, 2),
                currency=currency,
                effort=Effort.medium,
            )
        )

    if base_load is not None and base_load.share_of_total > 0.35:
        recs.append(
            Recommendation(
                title="Audit your always-on appliances",
                category=RecommendationCategory.behavioral,
                reason=(
                    f"About {round(base_load.share_of_total * 100)}% of your electricity is base load — "
                    "consumed even in your quietest months. Water heaters, old fridges and standby "
                    "devices are the usual culprits."
                ),
                estimated_savings=0.0,
                currency=currency,
                effort=Effort.low,
            )
        )

    if slab is not None:
        gap = slab.gap_to_next_slab
        if gap is None:
            recs.append(
                Recommendation(
                    title="You are in the top tariff slab",
                    category=RecommendationCategory.tariff,
                    reason="Every kWh you cut saves at the highest rate — efficiency pays most for you.",
                    estimated_savings=0.0,
                    currency=currency,
                    effort=Effort.low,
                )
            )
        elif latest.consumption > 0 and gap / latest.consumption <= 0.15:
            recs.append(
                Recommendation(
                    title=f"You are {round(gap)} kWh from the next tariff slab",
                    category=RecommendationCategory.tariff,
                    reason="Staying under the threshold keeps your marginal rate down — small cuts matter most right now.",
                    estimated_savings=0.0,
                    currency=currency,
                    effort=Effort.low,
                )
            )

    return recs


def build_report(
    property_id: int,
    utility_type: UtilityType,
    points: list[DatedBillPoint],
    *,
    unit: str | None = None,
    currency: str = "OMR",
    z_threshold: float = 2.0,
    floor_ratio_threshold: float = 1.3,
) -> HealthReport:
    """Build the Health Report for one utility.

    `points` must be ordered oldest→newest.
    """
    if len(points) < MIN_PERIODS:
        raise ValueError(f"at least {MIN_PERIODS} bills are required for a health report")

    unit = unit or DEFAULT_UNITS[utility_type]
    timeline = _timeline(utility_type, points, z_threshold)
    floor = _floor_rise(points, floor_ratio_threshold)
    base_load = _base_load(points) if utility_type == UtilityType.electricity else None

    slab = None
    if utility_type == UtilityType.electricity:
        latest = points[-1]
        slab = SlabPosition(
            marginal_rate=electricity_marginal_rate(
                latest.consumption, year=latest.period_start.year, month=latest.period_start.month
            ),
            gap_to_next_slab=next_slab_gap(latest.consumption),
        )

    return HealthReport(
        property_id=property_id,
        utility_type=utility_type,
        periods_analyzed=len(points),
        unit=unit,
        currency=currency,
        headline_annual_waste=round(sum(e.excess_cost for e in timeline), 2),
        base_load=base_load,
        floor_rise=floor,
        slab=slab,
        timeline=timeline,
        recommendations=_recommendations(utility_type, points, floor, base_load, slab, currency),
    )
