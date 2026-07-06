from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import DbSession, OwnedProperty
from app.models.bill import Bill
from app.schemas.bill import BillCreate, BillRead
from app.services.analysis import DEFAULT_UNITS

router = APIRouter(prefix="/properties/{property_id}/bills", tags=["bills"])


@router.post("", response_model=BillRead, status_code=status.HTTP_201_CREATED)
def create_bill(payload: BillCreate, prop: OwnedProperty, db: DbSession) -> Bill:
    unit = payload.unit or DEFAULT_UNITS[payload.utility_type]
    bill = Bill(
        property_id=prop.id,
        utility_type=payload.utility_type,
        period_start=payload.period_start,
        period_end=payload.period_end,
        consumption=payload.consumption,
        unit=unit,
        cost=payload.cost,
        currency=payload.currency,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


@router.get("", response_model=list[BillRead])
def list_bills(prop: OwnedProperty, db: DbSession) -> list[Bill]:
    stmt = select(Bill).where(Bill.property_id == prop.id).order_by(Bill.period_end.asc())
    return list(db.scalars(stmt))
