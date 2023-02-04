from typing import Any

from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlmodel import Session

from tubecast import crud, models, settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def get_password_hash(password: str) -> str:
    """
    Get password hash from a plain password.

    Args:
        password (str): Plain password to be hashed.

    Returns:
        str: Hashed password.
    """
    return str(password_context.hash(secret=password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password (str): Plain password.
        hashed_password (str): Hashed password.

    Returns:
        bool: True if plain password matches the hashed password, False otherwise.
    """
    return bool(password_context.verify(secret=plain_password, hash=hashed_password))


def encode_token(
    subject: str | Any, key: str, expires_delta: timedelta, fresh: bool = False
) -> str:
    """
    Encode subject in token

    Args:
        subject (str): subject to be encoded
        key (str): secret key
        expires_delta (timedelta): token expiration time.
        fresh (bool): whether the token is fresh or not. Defaults to False.

    Returns:
        token (str): encoded token
    """
    payload = {
        "exp": datetime.utcnow() + expires_delta,
        "iat": datetime.utcnow(),
        "sub": str(subject),
        "fresh": fresh,
    }
    return jwt.encode(payload=payload, key=key, algorithm=settings.ALGORITHM)


def decode_token(
    token: str,
    key: str,
) -> str:
    """
    Decode token to get subject

    Args:
        token (str): encoded token
        key (str): secret key

    Returns:
        str: subject from token

    Raises:
        HTTPException: when token is expired or invalid.
    """
    try:
        payload: dict[str, str] = jwt.decode(jwt=token, key=key, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired Token") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token") from e
    return payload["sub"]


async def get_tokens(user_id: str, fresh: bool = False) -> models.Tokens:
    """
    Get access and refresh tokens for a user.

    Args:
        user_id (str): The user id.
        fresh (bool): Whether the token is fresh or not. Defaults to False.

    Returns:
        models.Tokens: The tokens.
    """
    access_token = encode_token(
        subject=user_id,
        key=settings.JWT_ACCESS_SECRET_KEY,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        fresh=fresh,
    )
    refresh_token = encode_token(
        subject=user_id,
        key=settings.JWT_REFRESH_SECRET_KEY,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        fresh=fresh,
    )
    return models.Tokens(access_token=access_token, refresh_token=refresh_token)


async def get_tokens_from_username_password(
    db: Session, form_data: OAuth2PasswordRequestForm
) -> models.Tokens:
    """
    Get access and refresh tokens from a username and password.

    Args:
        db (Session): The database session.
        form_data (OAuth2PasswordRequestForm): the username and password

    Returns:
        models.Tokens: a dictionary with the access token and refresh token

    Raises:
        HTTPException: if the username or password is incorrect.
        HTTPException: if the user is inactive.
    """
    user = await crud.user.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password"
        )
    if not crud.user.is_active(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    # Create the tokens
    return await get_tokens(user_id=user.id)


async def get_tokens_from_refresh_token(refresh_token: str) -> models.Tokens:
    """
    Get new access and refresh tokens from a refresh token.

    Args:
        refresh_token (str): the refresh token

    Returns:
        dict[str, str]: a dictionary with the access token and refresh token

    Raises:
        HTTPException: if the refresh token is invalid.
    """
    try:
        user_id = decode_token(token=refresh_token, key=settings.JWT_REFRESH_SECRET_KEY)
    except HTTPException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token") from e

    # Create the tokens
    return await get_tokens(user_id=user_id, fresh=True)
