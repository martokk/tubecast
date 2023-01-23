from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from tubecast import crud, models, settings
from tubecast.api import deps
from tubecast.core import notify, security

router = APIRouter()


@router.post("/login/access-token", response_model=models.Tokens)
async def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> dict[str, str]:
    """
    OAuth2 compatible token login, get an access token for future requests

    Args:
        db (Session): The database session.
        form_data (OAuth2PasswordRequestForm): the username and password

    Returns:
        dict[str, str]: a dictionary with the access token and refresh token

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
    return {
        "access_token": security.encode_token(subject=user.id, key=settings.JWT_ACCESS_SECRET_KEY),
        "refresh_token": security.encode_token(
            subject=user.id, key=settings.JWT_REFRESH_SECRET_KEY
        ),
    }


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
        subject=user.id, key=settings.JWT_ACCESS_SECRET_KEY
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
