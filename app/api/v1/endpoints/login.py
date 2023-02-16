from typing import Any

from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic.networks import EmailStr
from sqlmodel import Session

from app import crud, models, settings
from app.api import deps
from app.core import notify, security

router = APIRouter()


@router.post("/login/access-token", response_model=models.Tokens)
async def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> models.Tokens:
    """
    Get new access and refresh tokens from a username and password.

    Args:
        db (Session): The database session.
        form_data (OAuth2PasswordRequestForm): the username and password

    Returns:
        models.Tokens: a dictionary with the access token and refresh token
    """
    return await security.get_tokens_from_username_password(db=db, form_data=form_data)


@router.post("/login/refresh-token", response_model=models.Tokens)
async def login_refresh_token(
    refresh_token: str = Body(...),
    db: Session = Depends(deps.get_db),
) -> models.Tokens:
    """
    Get new access and refresh tokens from a refresh token.

    Args:
        db (Session): The database session.
        refresh_token (str): the refresh token

    Returns:
        models.Tokens: a dictionary with the access token and refresh token
    """
    return await security.get_tokens_from_refresh_token(refresh_token=refresh_token)


@router.post("/login/test-token", response_model=models.UserRead)
async def test_token(current_user: models.User = Depends(deps.get_current_user)) -> models.User:
    """
    Test access token

    Args:
        current_user (models.User): The current user.

    Returns:
        Any: The current user.
    """
    return current_user


@router.post("/password-recovery/{username}", response_model=models.Msg)
async def recover_password(
    username: str, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)
) -> Any:
    """
    Password recovery endpoint.

    Args:
        username (str): The email of the user.
        background_tasks (BackgroundTasks): The background tasks.
        db (Session): The database session.

    Returns:
        Any: A message that the email was sent.

    Raises:
        HTTPException: if the user does not exist.

    """
    user = await crud.user.get_or_none(db, username=username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this username does not exist in the system.",
        )

    # Handle inactive user
    if not crud.user.is_active(user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    # Send email with password recovery link
    password_reset_token = security.encode_token(
        subject=user.id,
        key=settings.JWT_ACCESS_SECRET_KEY,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    background_tasks.add_task(
        notify.send_reset_password_email,
        email_to=user.email,
        username=username,
        token=password_reset_token,
    )

    return {"msg": "Password recovery email sent"}


@router.post("/reset-password")
async def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password endpoint.

    Args:
        token (str): The token to reset the password.
        new_password (str): The new password.
        db (Session): The database session.

    Returns:
        Any: A message that the password was updated.

    Raises:
        HTTPException: if the token is invalid.
        HTTPException: if the user does not exist.
        HTTPException: if the user is inactive.
    """
    # Verify the token
    user_id = security.decode_token(token=token, key=settings.JWT_ACCESS_SECRET_KEY)

    # Get the user
    user = await crud.user.get_or_none(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The user with user_id ({user_id}) does not exist in the system.",
        )

    # Check if the user is active
    if not crud.user.is_active(user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    # Update the password
    user.hashed_password = security.get_password_hash(new_password)

    # Save the user
    db.add(user)
    db.commit()

    return {"msg": "Password updated successfully"}


@router.post("/register", response_model=models.UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_open(
    *,
    db: Session = Depends(deps.get_db),
    username: str = Body(...),
    password: str = Body(...),
    email: EmailStr = Body(...),
    full_name: str = Body(None),
    background_tasks: BackgroundTasks,
) -> models.User:
    """
    Create new user without the need to be logged in.

    Args:
        db (Session): database session.
        username (str): username.
        password (str): password.
        email (EmailStr): email.
        full_name (str): full name.
        background_tasks (BackgroundTasks): background tasks.

    Returns:
        models.User: Created user.

    Raises:
        HTTPException: if user already exists.
        HTTPException: if open registration is forbidden.
    """
    if not settings.USERS_OPEN_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Open user registration is forbidden on this server",
        )
    user = await crud.user.get_or_none(db, username=username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user with this username already exists in the system",
        )
    user_in = models.UserCreateWithPassword(
        username=username, password=password, email=email, full_name=full_name
    )
    user = await crud.user.create_with_password(db, obj_in=user_in)

    # Sends email
    if settings.EMAILS_ENABLED and user_in.email:
        background_tasks.add_task(  # pragma: no cover
            notify.send_new_account_email,
            email_to=user_in.email,
            username=user_in.username,
            password=user_in.password,
        )

    return user
