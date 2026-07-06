"""Core consumption-analysis engine.

Deliberately dependency-light and decoupled from the ORM: it operates on plain
`BillPoint` values and returns a validated `AnalysisResult`. This keeps the logic
unit-testable without a database and keeps all savings figures deterministic and
auditable (the LLM layer, added later, only *phrases* these numbers — it never
invents them).
"""

import statistics
from dataclasses import dataclass

from app.models.bill import UtilityType
from app.schemas.analysis import (
    AnalysisResult,
    Baseline,
    ConsumptionStatus,
    Effort,
    Forecast,
    LatestAssessment,
    LeakAssessment,
    Recommendation,
    RecommendationCategory,
)

DEFAULT_UNITS = {UtilityType.water: "m3", UtilityType.electricity: "kWh"}
WARNING_Z = 1.0


@dataclass(frozen=True)
class BillPoint:
    consumption: float
    cost: float


def _unit_rate(latest: BillPoint) -> float:
    """Cost per unit derived from the latest bill (0 if consumption is 0)."""
    return latest.cost / latest.consumption if latest.consumption > 0 else 0.0


def _forecast(points: list[BillPoint], stdev: float, unit_rate: float, unit: str, currency: str) -> Forecast:
    recent = points[-3:]
    predicted = statistics.fmean(p.consumption for p in recent)
    band = stdev if stdev > 0 else predicted * 0.15
    predicted_cost = predicted * unit_rate if unit_rate > 0 else points[-1].cost
    method = "moving-average(3)" if len(points) >= 3 else "naive"
    return Forecast(
        predicted_consumption=round(predicted, 2),
        predicted_cost=round(predicted_cost, 2),
        currency=currency,
        unit=unit,
        method=method,
        low=round(max(0.0, predicted - band), 2),
        high=round(predicted + band, 2),
    )


def _leak_assessment(
    utility_type: UtilityType, ratio: float | None, leak_ratio_threshold: float
) -> LeakAssessment:
    if ratio is None or ratio < leak_ratio_threshold:
        return LeakAssessment(suspected=False, reason="Consumption is within the expected range of your history.")

    if utility_type == UtilityType.water:
        return LeakAssessment(
            suspected=True,
            reason=f"Water use is {round((ratio - 1) * 100)}% above your baseline, a pattern consistent with a leak.",
            verification_step="Close all taps and check whether the water meter is still turning.",
        )
    return LeakAssessment(
        suspected=True,
        reason=(
            f"Electricity use is {round((ratio - 1) * 100)}% above your baseline, which can indicate "
            "a faulty appliance or high standby/phantom load."
        ),
        verification_step="Check your overnight (all-off) baseline load for anything drawing power unexpectedly.",
    )


def _build_recommendations(
    utility_type: UtilityType,
    status: ConsumptionStatus,
    leak: LeakAssessment,
    excess_cost: float,
    currency: str,
) -> list[Recommendation]:
    recs: list[Recommendation] = []

    if leak.suspected:
        recs.append(
            Recommendation(
                title=(
                    "Investigate a suspected water leak"
                    if utility_type == UtilityType.water
                    else "Investigate a faulty appliance or standby load"
                ),
                category=RecommendationCategory.maintenance,
                reason=leak.reason,
                estimated_savings=round(excess_cost, 2),
                currency=currency,
                effort=Effort.medium,
            )
        )
    elif status in (ConsumptionStatus.warning, ConsumptionStatus.anomaly):
        recs.append(
            Recommendation(
                title="Bring usage back toward your normal range",
                category=RecommendationCategory.behavioral,
                reason="This period is above your usual consumption without a clear leak signature.",
                estimated_savings=round(excess_cost, 2),
                currency=currency,
                effort=Effort.low,
            )
        )

    # Always offer at least one general, profile-appropriate tip.
    if utility_type == UtilityType.water:
        recs.append(
            Recommendation(
                title="Install low-flow fixtures on taps and showerheads",
                category=RecommendationCategory.upgrade,
                reason="Low-flow fixtures cut water use with no change in habits.",
                estimated_savings=0.0,
                currency=currency,
                effort=Effort.low,
            )
        )
    else:
        recs.append(
            Recommendation(
                title="Set AC to 24°C and service the unit before summer",
                category=RecommendationCategory.behavioral,
                reason="Cooling dominates electricity use in the Gulf; each degree lower raises consumption.",
                estimated_savings=0.0,
                currency=currency,
                effort=Effort.low,
            )
        )

    return recs


def analyze(
    property_id: int,
    utility_type: UtilityType,
    points: list[BillPoint],
    *,
    unit: str | None = None,
    currency: str = "OMR",
    z_threshold: float = 2.0,
    leak_ratio_threshold: float = 1.4,
) -> AnalysisResult:
    """Analyze a property's bill history for one utility.

    `points` must be ordered oldest→newest; the last element is the period under review.
    """
    if not points:
        raise ValueError("at least one bill is required to analyze")

    unit = unit or DEFAULT_UNITS[utility_type]
    latest = points[-1]
    prior = points[:-1]
    unit_rate = _unit_rate(latest)

    # Baseline is built from PRIOR periods so the latest bill is judged against its own history.
    if len(prior) >= 2:
        mean = statistics.fmean(p.consumption for p in prior)
        stdev = statistics.stdev(p.consumption for p in prior)
    elif len(prior) == 1:
        mean, stdev = prior[0].consumption, 0.0
    else:
        mean, stdev = latest.consumption, 0.0

    baseline = Baseline(sample_size=len(prior), mean=round(mean, 2), stdev=round(stdev, 2))

    z: float | None = (latest.consumption - mean) / stdev if stdev > 0 else None
    ratio: float | None = latest.consumption / mean if mean > 0 else None

    if len(prior) < 2:
        status = ConsumptionStatus.insufficient_data
        message = "Not enough history yet — add more bills to unlock anomaly detection."
    elif z is not None:
        if z >= z_threshold:
            status = ConsumptionStatus.anomaly
        elif z >= WARNING_Z:
            status = ConsumptionStatus.warning
        else:
            status = ConsumptionStatus.normal
        message = _status_message(status, ratio)
    else:
        # Zero variance in history: fall back to a ratio comparison.
        if ratio is not None and ratio >= 1.5:
            status = ConsumptionStatus.anomaly
        elif ratio is not None and ratio >= 1.2:
            status = ConsumptionStatus.warning
        else:
            status = ConsumptionStatus.normal
        message = _status_message(status, ratio)

    latest_assessment = LatestAssessment(
        consumption=latest.consumption,
        unit=unit,
        status=status,
        z_score=round(z, 2) if z is not None else None,
        ratio_to_baseline=round(ratio, 2) if ratio is not None else None,
        message=message,
    )

    # Leak signal only meaningful once a baseline exists.
    leak = (
        _leak_assessment(utility_type, ratio, leak_ratio_threshold)
        if len(prior) >= 2
        else LeakAssessment(suspected=False, reason="Not enough history to assess leaks yet.")
    )

    excess_cost = max(0.0, latest.consumption - mean) * unit_rate
    recommendations = _build_recommendations(utility_type, status, leak, excess_cost, currency)
    forecast = _forecast(points, stdev, unit_rate, unit, currency)

    return AnalysisResult(
        property_id=property_id,
        utility_type=utility_type,
        baseline=baseline,
        latest=latest_assessment,
        leak=leak,
        forecast=forecast,
        recommendations=recommendations,
    )


def _status_message(status: ConsumptionStatus, ratio: float | None) -> str:
    pct = f"{round((ratio - 1) * 100)}%" if ratio is not None else "notably"
    if status == ConsumptionStatus.anomaly:
        return f"This period is {pct} above your baseline — an unusual spike worth investigating."
    if status == ConsumptionStatus.warning:
        return f"This period is {pct} above your baseline — keep an eye on it."
    return "This period is in line with your normal consumption."
