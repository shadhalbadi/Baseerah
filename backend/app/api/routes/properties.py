from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, OwnedProperty
from app.models.property import Property
from app.schemas.property import PropertyCreate, PropertyRead

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(payload: PropertyCreate, user: CurrentUser, db: DbSession) -> Property:
    prop = Property(user_id=user.id, **payload.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


@router.get("", response_model=list[PropertyRead])
def list_properties(user: CurrentUser, db: DbSession) -> list[Property]:
    return list(db.scalars(select(Property).where(Property.user_id == user.id)))


@router.get("/{property_id}", response_model=PropertyRead)
def get_property(prop: OwnedProperty) -> Property:
    return prop
