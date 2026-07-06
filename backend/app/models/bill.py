import enum
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UtilityType(str, enum.Enum):
    water = "water"
    electricity = "electricity"


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    utility_type: Mapped[UtilityType] = mapped_column(Enum(UtilityType), index=True)

    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)

    # consumption in the utility's native unit (m3 for water, kWh for electricity)
    consumption: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(16))

    cost: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="OMR")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    property: Mapped["Property"] = relationship(back_populates="bills")  # noqa: F821
