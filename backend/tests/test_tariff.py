"""Table-driven tests for the Oman residential electricity tariff engine.

Money code: covers clean, boundary, discount, and error cases explicitly.
Rates: APSR residential slabs (14/18/32 bz per kWh at 4,000/6,000 kWh monthly
thresholds) and the APSR summer-2026 relief program (May: 15/10/5%,
Jun-Aug: 20/15/10% discounts per slab).
"""

import pytest

from app.services.tariff import electricity_cost, electricity_marginal_rate, next_slab_gap


@pytest.mark.parametrize(
    "kwh, year, month, expected_cost",
    [
        # zero consumption -> zero cost
        (0, 2026, 1, 0.0),
        # entirely within first slab: 1000 * 0.014
        (1000, 2026, 1, 14.0),
        # exact first-slab boundary: 4000 * 0.014
        (4000, 2026, 1, 56.0),
        # just past the boundary: 56.0 + 1 * 0.018
        (4001, 2026, 1, 56.018),
        # spanning all three slabs: 4000*0.014 + 2000*0.018 + 1000*0.032
        (7000, 2026, 1, 124.0),
        # May 2026 relief: 15/10/5% per slab -> 1000 kWh all in slab 1
        (1000, 2026, 5, 11.9),
        # June 2026 relief: 20/15/10% -> 56*0.80 + 36*0.85 + 32*0.90
        (7000, 2026, 6, 104.2),
        # August 2026 relief same as June
        (7000, 2026, 8, 104.2),
        # summer month in a non-relief year -> standard rates
        (1000, 2025, 6, 14.0),
        # September 2026 -> relief ended, standard rates
        (1000, 2026, 9, 14.0),
    ],
)
def test_electricity_cost(kwh, year, month, expected_cost):
    assert electricity_cost(kwh, year=year, month=month) == pytest.approx(expected_cost)


@pytest.mark.parametrize(
    "kwh, year, month, expected_rate",
    [
        # slab 1
        (3000, 2026, 1, 0.014),
        # slab 2
        (5000, 2026, 1, 0.018),
        # slab 3
        (8000, 2026, 1, 0.032),
        # boundary consumption sits in the slab it filled
        (4000, 2026, 1, 0.014),
        (4001, 2026, 1, 0.018),
        # June 2026 relief applies to the marginal slab: 0.014 * 0.80
        (3000, 2026, 6, 0.0112),
        # zero consumption -> marginal rate of the first slab
        (0, 2026, 1, 0.014),
    ],
)
def test_electricity_marginal_rate(kwh, year, month, expected_rate):
    assert electricity_marginal_rate(kwh, year=year, month=month) == pytest.approx(expected_rate)


@pytest.mark.parametrize(
    "kwh, expected_gap",
    [
        # 3660 kWh -> 340 kWh from the 4000 threshold
        (3660, 340.0),
        # already in slab 2 -> 1000 from the 6000 threshold
        (5000, 1000.0),
        # top slab -> no next threshold
        (8000, None),
        (4000, 2000.0),
    ],
)
def test_next_slab_gap(kwh, expected_gap):
    assert next_slab_gap(kwh) == expected_gap


@pytest.mark.parametrize("bad_kwh", [-1, -0.01])
def test_negative_consumption_rejected(bad_kwh):
    with pytest.raises(ValueError):
        electricity_cost(bad_kwh, year=2026, month=1)
    with pytest.raises(ValueError):
        electricity_marginal_rate(bad_kwh, year=2026, month=1)


@pytest.mark.parametrize("bad_month", [0, 13])
def test_invalid_month_rejected(bad_month):
    with pytest.raises(ValueError):
        electricity_cost(1000, year=2026, month=bad_month)
