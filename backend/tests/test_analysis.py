"""Table-driven tests for the consumption-analysis engine.

Savings figures drive user-facing money recommendations, so these paths are
covered explicitly: clean, warning, anomaly, leak, and cold-start cases.
"""

import pytest

from app.models.bill import UtilityType
from app.schemas.analysis import ConsumptionStatus
from app.services.analysis import BillPoint, analyze


def _points(consumptions: list[float], rate: float = 1.0) -> list[BillPoint]:
    return [BillPoint(consumption=c, cost=c * rate) for c in consumptions]


@pytest.mark.parametrize(
    "consumptions, expected_status",
    [
        # prior [10,12,8,10] -> mean 10, stdev ~1.63; latest in-line -> normal
        ([10, 12, 8, 10, 10], ConsumptionStatus.normal),
        # latest 12 -> z ~1.22 (1 <= z < 2) -> warning
        ([10, 12, 8, 10, 12], ConsumptionStatus.warning),
        # latest 15 -> z ~3.06 (>= 2) -> anomaly
        ([10, 12, 8, 10, 15], ConsumptionStatus.anomaly),
        # only one prior bill -> insufficient data
        ([10, 12], ConsumptionStatus.insufficient_data),
    ],
)
def test_status_classification(consumptions, expected_status):
    result = analyze(1, UtilityType.electricity, _points(consumptions))
    assert result.latest.status == expected_status


def test_requires_at_least_one_bill():
    with pytest.raises(ValueError):
        analyze(1, UtilityType.water, [])


def test_water_leak_flagged_with_verification_step():
    # baseline ~10 m3, latest 20 m3 -> ratio 2.0 >= leak threshold
    result = analyze(1, UtilityType.water, _points([10, 10, 10, 10, 20]))
    assert result.leak.suspected is True
    assert result.leak.verification_step is not None
    assert "meter" in result.leak.verification_step.lower()


def test_no_leak_when_within_range():
    result = analyze(1, UtilityType.water, _points([10, 10, 11, 10, 10]))
    assert result.leak.suspected is False


def test_estimated_savings_equals_excess_cost():
    # baseline mean = 10, latest = 20, rate = 2.5 -> excess cost = (20-10)*2.5 = 25
    result = analyze(1, UtilityType.water, _points([10, 10, 10, 10, 20], rate=2.5))
    leak_rec = next(r for r in result.recommendations if r.category.value == "maintenance")
    assert leak_rec.estimated_savings == pytest.approx(25.0)


def test_forecast_uses_moving_average_of_recent():
    # last three consumptions: 12, 14, 16 -> mean 14
    result = analyze(1, UtilityType.electricity, _points([10, 10, 12, 14, 16]))
    assert result.forecast.method == "moving-average(3)"
    assert result.forecast.predicted_consumption == pytest.approx(14.0)
    assert result.forecast.low <= result.forecast.predicted_consumption <= result.forecast.high


def test_always_returns_at_least_one_recommendation():
    result = analyze(1, UtilityType.electricity, _points([10, 10, 10, 10, 10]))
    assert len(result.recommendations) >= 1


def test_default_unit_by_utility():
    water = analyze(1, UtilityType.water, _points([10, 10, 10]))
    elec = analyze(1, UtilityType.electricity, _points([10, 10, 10]))
    assert water.latest.unit == "m3"
    assert elec.latest.unit == "kWh"
