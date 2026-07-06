from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.property import PropertyType


class PropertyCreate(BaseModel):
    name: str
    type: PropertyType = PropertyType.apartment
    size_sqm: float | None = None
    occupants: int | None = None
    region: str | None = None


class PropertyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    type: PropertyType
    size_sqm: float | None
    occupants: int | None
    region: str | None
    created_at: datetime
