from collections.abc import Generator

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app import crud, models, settings
from app.core import security
from app.db.session import SessionLocal


class RedirectException(HTTPException):
    def __init__(self, url: str, status_code: int = 307):
        super().__init__(status_code=status_code, headers={"Location": url})


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


async def get_tokens_from_cookie(
    access_token: str | None = Cookie(None), refresh_token: str | None = Cookie(None)
) -> models.Tokens:
    """
    Gets the tokens from the cookie.

    Args:
        access_token (str | None): The access token.
        refresh_token (str | None): The refresh token.

    Returns:
        models.Tokens: The tokens.
    """
    access_token_value = (
        access_token.split("Bearer ")[1] if access_token and "Bearer" in access_token else None
    )
    refresh_token_value = (
        refresh_token.split("Bearer ")[1] if refresh_token and "Bearer" in refresh_token else None
    )
    return models.Tokens(access_token=access_token_value, refresh_token=refresh_token_value)


async def get_tokens_from_refresh_token(refresh_token: str) -> models.Tokens | None:
    """
    Gets new tokens from a refresh token. Sets the new tokens in the cookie.

    Args:
        refresh_token (str): The refresh token.

    Returns:
        models.Tokens: The tokens.
    """
    try:
        new_tokens = await security.get_tokens_from_refresh_token(refresh_token=refresh_token)
    except HTTPException:
        return None

    # Set the tokens in the cookie
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token", value=f"Bearer {new_tokens.access_token}", httponly=True
    )
    response.set_cookie(
        key="refresh_token", value=f"Bearer {new_tokens.refresh_token}", httponly=True
    )

    return new_tokens


async def get_current_tokens(
    tokens: models.Tokens = Depends(get_tokens_from_cookie), db: Session = Depends(get_db)
) -> models.Tokens | None:
    """
    Gets the current tokens. If the access token is
    invalid or not found in cookie, returns None.

    Args:
        tokens (models.Tokens): The tokens.
        db (Session): The database session.

    Returns:
        models.Tokens | None: The current tokens.
    """
    try:
        # Try to decode the access token
        security.decode_token(token=str(tokens.access_token), key=settings.JWT_ACCESS_SECRET_KEY)
    except HTTPException:
        # If the access token is invalid, regenerate new tokens from refresh token
        if not tokens.refresh_token:
            return None
        try:
            new_tokens = await get_tokens_from_refresh_token(refresh_token=tokens.refresh_token)
            if new_tokens:
                return new_tokens
            else:
                return None

        except HTTPException:  # pragma: no cover
            return None

    return tokens


async def get_current_user(
    tokens: models.Tokens = Depends(get_tokens_from_cookie), db: Session = Depends(get_db)
) -> models.User | None:
    """
    Gets the current user. If the access token is
    invalid or not found in cookie, returns None.

    Args:
        tokens (models.Tokens): The tokens.
        db (Session): The database session.

    Returns:
        models.User | None: The current user.
    """
    # Get the user_id from the new access token
    try:
        user_id = security.decode_token(
            token=str(tokens.access_token), key=settings.JWT_ACCESS_SECRET_KEY
        )
    except HTTPException:
        return None

    return await crud.user.get(db=db, id=user_id)


async def get_current_user_or_raise(
    current_user: models.User | None = Depends(get_current_user),
) -> models.User | None:
    """
    Gets the current user. If the user is not found, raises an exception.

    Args:
        current_user (models.User | None): The current user.

    Returns:
        models.User | None: The current user.

    Raises:
        HTTPException: If the user is not found.
    """
    if not current_user:
        raise RedirectException(url="/login")
    return current_user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user_or_raise),
) -> models.User:
    """
    Gets the current active user.

    Args:
        current_user (models.User): The current user.

    Returns:
        models.User: The current active user.

    Raises:
        HTTPException: If the user is inactive.
    """
    if not current_user:
        raise RedirectException(url="/login")
    if not crud.user.is_active(current_user):
        raise RedirectException(url="/login")

    return current_user


async def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user_or_raise),
) -> models.User:
    """
    Gets the current active superuser.

    Args:
        current_user (models.User): The current user.

    Returns:
        models.User: The current active superuser.

    Raises:
        HTTPException: If the user is not a superuser.
    """
    if not current_user:
        raise RedirectException(url="/login")
    if not crud.user.is_superuser(user_=current_user):
        raise RedirectException(url="/login")
    return current_user
