from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property import Property
from app.models.user import User
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    subject = decode_token(token)
    if subject is None:
        raise _CREDENTIALS_EXC
    try:
        user_id = int(subject)
    except ValueError:
        raise _CREDENTIALS_EXC
    user = db.get(User, user_id)
    if user is None:
        raise _CREDENTIALS_EXC
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


def get_owned_property(property_id: int, user: CurrentUser, db: DbSession) -> Property:
    """Load a property and enforce that it belongs to the current user.

    Returns 404 (not 403) for a property owned by someone else so we don't leak
    which property ids exist.
    """
    prop = db.get(Property, property_id)
    if prop is None or prop.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="property not found")
    return prop


OwnedProperty = Annotated[Property, Depends(get_owned_property)]
