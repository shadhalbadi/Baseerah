"""Table-driven tests for the Home Utility Health Report engine.

The headline waste figure drives the report's money claim, so pricing paths
(marginal tariff for electricity, unit rate for water) are covered explicitly.
"""

from datetime import date

import pytest

from app.models.bill import UtilityType
from app.schemas.analysis import ConsumptionStatus
from app.services.report import DatedBillPoint, build_report

WATER_RATE = 2.0  # OMR per m3 used to derive costs in water fixtures


def _monthly_points(
    consumptions: list[float],
    *,
    start_year: int = 2025,
    start_month: int = 1,
    rate: float | None = None,
    costs: list[float] | None = None,
) -> list[DatedBillPoint]:
    points = []
    year, month = start_year, start_month
    for i, c in enumerate(consumptions):
        next_month = month % 12 + 1
        next_year = year + (1 if month == 12 else 0)
        cost = costs[i] if costs is not None else c * (rate if rate is not None else 1.0)
        points.append(
            DatedBillPoint(
                period_start=date(year, month, 1),
                period_end=date(next_year, next_month, 1),
                consumption=c,
                cost=cost,
            )
        )
        year, month = next_year, next_month
    return points


def test_requires_six_periods():
    with pytest.raises(ValueError):
        build_report(1, UtilityType.water, _monthly_points([10] * 5, rate=WATER_RATE))


def test_flat_history_reports_zero_waste_and_no_signals():
    report = build_report(1, UtilityType.water, _monthly_points([10] * 12, rate=WATER_RATE))
    assert report.headline_annual_waste == pytest.approx(0.0)
    assert report.floor_rise.suspected is False
    assert all(e.status == ConsumptionStatus.normal for e in report.timeline)


def test_timeline_flags_historical_spike_with_priced_excess():
    # electricity, all within slab 1 (14 bz marginal) in non-relief months
    consumptions = [1000, 1000, 1000, 1000, 1000, 1000, 2000, 1000, 1000, 1000, 1000, 1000]
    points = _monthly_points(consumptions, start_year=2025, rate=0.014)
    report = build_report(1, UtilityType.electricity, points)
    spike = next(e for e in report.timeline if e.consumption == 2000)
    assert spike.status == ConsumptionStatus.anomaly
    # excess = (2000 - 1000 baseline) * 0.014 marginal rate
    assert spike.excess_cost == pytest.approx(14.0)
    assert report.headline_annual_waste == pytest.approx(14.0)


def test_water_excess_priced_at_unit_rate():
    consumptions = [10, 10, 10, 10, 10, 10, 20, 10, 10, 10, 10, 10]
    report = build_report(1, UtilityType.water, _monthly_points(consumptions, rate=WATER_RATE))
    spike = next(e for e in report.timeline if e.consumption == 20)
    # excess = (20 - 10) * 2.0 OMR/m3
    assert spike.excess_cost == pytest.approx(20.0)


def test_floor_rise_detects_continuous_leak():
    # prior floor 10, every one of the last 6 periods >= 14 -> ratio 1.4
    consumptions = [10, 12, 11, 10, 12, 11, 14, 15, 14, 16, 15, 14]
    report = build_report(1, UtilityType.water, _monthly_points(consumptions, rate=WATER_RATE))
    assert report.floor_rise.suspected is True
    assert report.floor_rise.prior_floor == pytest.approx(10.0)
    assert report.floor_rise.recent_floor == pytest.approx(14.0)
    assert report.floor_rise.ratio == pytest.approx(1.4)
    # a leak recommendation carries the annualized floor-rise cost: (14-10)*2.0*12
    leak_rec = next(r for r in report.recommendations if r.category.value == "maintenance")
    assert leak_rec.estimated_savings == pytest.approx(96.0)


def test_no_floor_rise_when_floor_stable():
    consumptions = [10, 14, 12, 10, 15, 11, 10, 16, 13, 10, 14, 12]
    report = build_report(1, UtilityType.water, _monthly_points(consumptions, rate=WATER_RATE))
    assert report.floor_rise.suspected is False


def test_base_load_estimated_from_lowest_months_electricity_only():
    # winter months 500/500/600, summer up to 2000
    consumptions = [500, 500, 600, 900, 1400, 1800, 2000, 1900, 1500, 1000, 700, 500]
    elec = build_report(1, UtilityType.electricity, _monthly_points(consumptions, rate=0.014))
    assert elec.base_load is not None
    # mean of the three lowest months: (500 + 500 + 500) / 3
    assert elec.base_load.monthly_consumption == pytest.approx(500.0)
    assert 0 < elec.base_load.share_of_total < 1

    water = build_report(1, UtilityType.water, _monthly_points(consumptions, rate=WATER_RATE))
    assert water.base_load is None


def test_slab_position_reported_for_electricity():
    consumptions = [3000, 3100, 3200, 3300, 3500, 3660]
    report = build_report(1, UtilityType.electricity, _monthly_points(consumptions, rate=0.014))
    assert report.slab is not None
    assert report.slab.gap_to_next_slab == pytest.approx(340.0)
    assert report.slab.marginal_rate == pytest.approx(0.014)

    water = build_report(1, UtilityType.water, _monthly_points([10] * 6, rate=WATER_RATE))
    assert water.slab is None


def test_metadata_passthrough():
    report = build_report(
        7, UtilityType.water, _monthly_points([10] * 6, rate=WATER_RATE), unit="m3", currency="OMR"
    )
    assert report.property_id == 7
    assert report.periods_analyzed == 6
    assert report.unit == "m3"
    assert report.currency == "OMR"
