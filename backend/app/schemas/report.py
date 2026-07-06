from datetime import date

from pydantic import BaseModel

from app.models.bill import UtilityType
from app.schemas.analysis import ConsumptionStatus, Recommendation


class BaseLoadEstimate(BaseModel):
    """Always-on consumption inferred from the lowest months (electricity)."""

    monthly_consumption: float
    monthly_cost: float
    share_of_total: float  # fraction of analyzed consumption that is base load


class FloorRiseAssessment(BaseModel):
    """Continuous-flow leak signal: the consumption *floor* rising over time."""

    suspected: bool
    recent_floor: float
    prior_floor: float
    ratio: float | None
    reason: str


class TimelineEntry(BaseModel):
    period_start: date
    period_end: date
    consumption: float
    status: ConsumptionStatus
    excess_cost: float  # cost of consumption above the trailing baseline


class SlabPosition(BaseModel):
    """Where the latest period sits in the tariff slab structure (electricity)."""

    marginal_rate: float
    gap_to_next_slab: float | None  # kWh until the next, more expensive slab


class HealthReport(BaseModel):
    property_id: int
    utility_type: UtilityType
    periods_analyzed: int
    unit: str
    currency: str
    headline_annual_waste: float  # sum of timeline excess costs, marginal-priced
    base_load: BaseLoadEstimate | None  # electricity only
    floor_rise: FloorRiseAssessment
    slab: SlabPosition | None  # electricity only
    timeline: list[TimelineEntry]
    recommendations: list[Recommendation]
