from enum import Enum

from pydantic import BaseModel

from app.models.bill import UtilityType


class ConsumptionStatus(str, Enum):
    insufficient_data = "insufficient_data"
    normal = "normal"
    warning = "warning"
    anomaly = "anomaly"


class RecommendationCategory(str, Enum):
    behavioral = "behavioral"
    maintenance = "maintenance"
    upgrade = "upgrade"
    tariff = "tariff"


class Effort(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Baseline(BaseModel):
    sample_size: int
    mean: float
    stdev: float


class LatestAssessment(BaseModel):
    consumption: float
    unit: str
    status: ConsumptionStatus
    z_score: float | None
    ratio_to_baseline: float | None
    message: str


class LeakAssessment(BaseModel):
    suspected: bool
    reason: str
    verification_step: str | None = None


class Forecast(BaseModel):
    predicted_consumption: float
    predicted_cost: float
    currency: str
    unit: str
    method: str
    low: float
    high: float


class Recommendation(BaseModel):
    title: str
    category: RecommendationCategory
    reason: str
    estimated_savings: float  # per period, in the bill's currency
    currency: str
    effort: Effort


class AnalysisResult(BaseModel):
    property_id: int
    utility_type: UtilityType
    baseline: Baseline
    latest: LatestAssessment
    leak: LeakAssessment
    forecast: Forecast
    recommendations: list[Recommendation]


class Explanation(BaseModel):
    enabled: bool  # false when no Anthropic API key is configured
    text: str | None
