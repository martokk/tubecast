from typing import Generator

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
    """
    Get the user id from the access token.

    Args:
        token (str): The access token.

    Returns:
        str: The user id.
    """
    return security.decode_token(token=token, key=settings.JWT_ACCESS_SECRET_KEY)


async def get_current_user(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> models.User:
    """
    Get the user from the access token.

    Args:
        db (Session): The database session.
        user_id (str): The user id.

    Returns:
        models.User: The user.

    Raises:
        HTTPException: If the user is not found.
    """
    try:
        return await crud.user.get(db=db, id=user_id)
    except crud.RecordNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User from access token not found"
        ) from exc


def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """ "
    Get the active user from the access token.

    Args:
        current_user (models.User): The user from the access token.

    Returns:
        models.User: The active user.

    Raises:
        HTTPException: If the user is not active.
    """
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Get the active superuser from the access token.

    Args:
        current_user (models.User): The user from the access token.

    Returns:
        models.User: The active superuser.

    Raises:
        HTTPException: If the user is not a superuser.
    """

    if not crud.user.is_superuser(user_=current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
        )
    return current_user
