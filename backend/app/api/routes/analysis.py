from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import DbSession, OwnedProperty
from app.config import get_settings
from app.models.bill import Bill, UtilityType
from app.models.property import Property
from app.schemas.analysis import AnalysisResult, Explanation
from app.services.analysis import BillPoint, analyze
from app.services.explain import explain, explanations_enabled

router = APIRouter(prefix="/properties/{property_id}/analysis", tags=["analysis"])


def _run_analysis(prop: Property, utility_type: UtilityType, db: Session) -> AnalysisResult:
    stmt = (
        select(Bill)
        .where(Bill.property_id == prop.id, Bill.utility_type == utility_type)
        .order_by(Bill.period_end.asc())
    )
    bills = list(db.scalars(stmt))
    if not bills:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"no {utility_type.value} bills found for this property",
        )

    settings = get_settings()
    points = [BillPoint(consumption=b.consumption, cost=b.cost) for b in bills]
    return analyze(
        property_id=prop.id,
        utility_type=utility_type,
        points=points,
        unit=bills[-1].unit,
        currency=bills[-1].currency,
        z_threshold=settings.anomaly_z_threshold,
        leak_ratio_threshold=settings.leak_ratio_threshold,
    )


@router.get("", response_model=AnalysisResult)
def analyze_property(prop: OwnedProperty, utility_type: UtilityType, db: DbSession) -> AnalysisResult:
    return _run_analysis(prop, utility_type, db)


@router.get("/explanation", response_model=Explanation)
def explain_property(
    prop: OwnedProperty,
    utility_type: UtilityType,
    db: DbSession,
    lang: str = Query("en", pattern="^(en|ar)$"),
) -> Explanation:
    result = _run_analysis(prop, utility_type, db)
    return Explanation(enabled=explanations_enabled(), text=explain(result, lang))
