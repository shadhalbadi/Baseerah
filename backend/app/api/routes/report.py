from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, OwnedProperty
from app.config import get_settings
from app.models.bill import Bill, UtilityType
from app.schemas.report import HealthReport
from app.services.report import DatedBillPoint, build_report

router = APIRouter(prefix="/properties/{property_id}/report", tags=["report"])


@router.get("", response_model=HealthReport)
def property_report(prop: OwnedProperty, utility_type: UtilityType, db: DbSession) -> HealthReport:
    stmt = (
        select(Bill)
        .where(Bill.property_id == prop.id, Bill.utility_type == utility_type)
        .order_by(Bill.period_end.asc())
    )
    bills = list(db.scalars(stmt))

    settings = get_settings()
    points = [
        DatedBillPoint(
            period_start=b.period_start,
            period_end=b.period_end,
            consumption=b.consumption,
            cost=b.cost,
        )
        for b in bills
    ]
    try:
        return build_report(
            property_id=prop.id,
            utility_type=utility_type,
            points=points,
            unit=bills[-1].unit if bills else None,
            currency=bills[-1].currency if bills else "OMR",
            z_threshold=settings.anomaly_z_threshold,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
