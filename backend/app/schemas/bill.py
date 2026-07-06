from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.bill import UtilityType


class BillCreate(BaseModel):
    utility_type: UtilityType
    period_start: date
    period_end: date
    consumption: float = Field(ge=0)
    unit: str | None = None  # defaults by utility type if omitted
    cost: float = Field(ge=0)
    currency: str = "OMR"

    @model_validator(mode="after")
    def _check_period(self) -> "BillCreate":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class BillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    property_id: int
    utility_type: UtilityType
    period_start: date
    period_end: date
    consumption: float
    unit: str
    cost: float
    currency: str
    created_at: datetime
