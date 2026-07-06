"""Oman residential electricity tariff engine.

Declarative slab table so savings figures are priced at the user's *marginal*
rate, not a blended average. Sources:
- APSR permitted residential tariffs (https://apsr.om/en/tariffs):
  14/18/32 baisa per kWh at 4,000 / 6,000 kWh monthly thresholds.
- APSR summer-2026 relief for single basic residential accounts
  (May: 15/10/5%, Jun-Aug: 20/15/10% discount per slab).

Slab thresholds are treated as monthly consumption. Verify against a real bill
before relying on cross-checks; the relief program is keyed to (year, month) so
standard rates apply automatically outside 2026.
"""

from dataclasses import dataclass

CURRENCY = "OMR"


@dataclass(frozen=True)
class Slab:
    upper: float | None  # cumulative kWh threshold; None = unbounded top slab
    rate: float  # OMR per kWh


ELECTRICITY_SLABS = (
    Slab(upper=4000, rate=0.014),
    Slab(upper=6000, rate=0.018),
    Slab(upper=None, rate=0.032),
)

# (year, month) -> per-slab discount fractions, aligned with ELECTRICITY_SLABS
_SUMMER_2026_MAY = (0.15, 0.10, 0.05)
_SUMMER_2026_PEAK = (0.20, 0.15, 0.10)
RELIEF_DISCOUNTS: dict[tuple[int, int], tuple[float, ...]] = {
    (2026, 5): _SUMMER_2026_MAY,
    (2026, 6): _SUMMER_2026_PEAK,
    (2026, 7): _SUMMER_2026_PEAK,
    (2026, 8): _SUMMER_2026_PEAK,
}


def _validate(kwh: float, month: int) -> None:
    if kwh < 0:
        raise ValueError("consumption cannot be negative")
    if not 1 <= month <= 12:
        raise ValueError("month must be 1-12")


def _slab_rates(year: int, month: int) -> list[tuple[float | None, float]]:
    discounts = RELIEF_DISCOUNTS.get((year, month), (0.0,) * len(ELECTRICITY_SLABS))
    return [(s.upper, s.rate * (1 - d)) for s, d in zip(ELECTRICITY_SLABS, discounts)]


def electricity_cost(kwh: float, *, year: int, month: int) -> float:
    """Consumption charge in OMR for one monthly billing period."""
    _validate(kwh, month)
    cost = 0.0
    lower = 0.0
    for upper, rate in _slab_rates(year, month):
        band_top = kwh if upper is None else min(kwh, upper)
        if band_top > lower:
            cost += (band_top - lower) * rate
        if upper is None or kwh <= upper:
            break
        lower = upper
    return cost


def electricity_marginal_rate(kwh: float, *, year: int, month: int) -> float:
    """OMR per kWh of the last unit consumed — the rate a saved unit is worth."""
    _validate(kwh, month)
    for upper, rate in _slab_rates(year, month):
        if upper is None or kwh <= upper:
            return rate
    raise AssertionError("unreachable: top slab is unbounded")


def next_slab_gap(kwh: float) -> float | None:
    """kWh remaining before the next (more expensive) slab; None in the top slab."""
    if kwh < 0:
        raise ValueError("consumption cannot be negative")
    for slab in ELECTRICITY_SLABS:
        if slab.upper is not None and kwh < slab.upper:
            return slab.upper - kwh
    return None
