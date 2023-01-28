from typing import Any

from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from passlib.context import CryptContext

from tubecast import logger, settings

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


def encode_token(subject: str | Any, key: str, expires_delta: timedelta | None = None) -> str:
    """
    Encode subject in token

    Args:
        subject (str): subject to be encoded
        key (str): secret key
        expires_delta (timedelta, optional): token expiration time. Defaults to None.

    Returns:
        token (str): encoded token
    """
    expires_delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "exp": datetime.utcnow() + expires_delta,
        "iat": datetime.utcnow(),
        "sub": str(subject),
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
        logger.warning("Expired Token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired Token") from e
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid Token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token") from e
    return payload["sub"]
