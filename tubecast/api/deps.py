from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from tubecast import crud, models, settings
from tubecast.core import security
from tubecast.db.session import SessionLocal

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/login/access-token")


def get_db() -> Generator[Session, None, None]:
    """
    A generator function that creates a new database session.

    Yields:
        Session: A new database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user_id(token: str = Depends(reusable_oauth2)) -> str:

    # Decode token
    user_id = security.decode_token(token=token, key=settings.JWT_ACCESS_SECRET_KEY)

    # Return User object
    return user_id


async def get_current_user(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> models.User:
    try:
        user = await crud.user.get(db=db, id=user_id)
    except crud.RecordNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User from access token not found"
        ) from e
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_superuser(user_=current_user):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user
