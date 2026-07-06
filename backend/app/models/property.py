import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PropertyType(str, enum.Enum):
    apartment = "apartment"
    villa = "villa"
    office = "office"
    shop = "shop"
    other = "other"


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[PropertyType] = mapped_column(Enum(PropertyType), default=PropertyType.apartment)
    size_sqm: Mapped[float | None] = mapped_column(Float, nullable=True)
    occupants: Mapped[int | None] = mapped_column(Integer, nullable=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    owner: Mapped["User"] = relationship(back_populates="properties")  # noqa: F821
    bills: Mapped[list["Bill"]] = relationship(  # noqa: F821
        back_populates="property", cascade="all, delete-orphan"
    )
