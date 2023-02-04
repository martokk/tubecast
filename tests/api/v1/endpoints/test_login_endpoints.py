from unittest.mock import patch

import jwt
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from tubecast import crud, models, settings


async def test_get_access_token(
    db_with_user: Session,
    client: TestClient,
) -> None:
    login_data = {
        "username": "test_user",
        "password": "test_password",
    }
    r = client.post(f"{settings.API_V1_PREFIX}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == status.HTTP_200_OK
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["access_token"]
    assert tokens["refresh_token"]


async def test_get_access_token_bad_password(client: TestClient) -> None:
    login_data = {
        "username": "test_user",
        "password": "bad_password",
    }
    r = client.post(f"{settings.API_V1_PREFIX}/login/access-token", data=login_data)
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
    assert r.json() == {"detail": "Incorrect username or password"}


async def test_get_access_token_bad_username(client: TestClient) -> None:
    login_data = {
        "username": "bad_user",
        "password": "test_password",
    }
    r = client.post(f"{settings.API_V1_PREFIX}/login/access-token", data=login_data)
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
    assert r.json() == {"detail": "Incorrect username or password"}


async def test_get_access_token_inactive_user(db_with_user: Session, client: TestClient) -> None:
    db_user = await crud.user.update(
        db=db_with_user, username="test_user", obj_in=models.UserUpdate(is_active=False)
    )
    login_data = {
        "username": "test_user",
        "password": "test_password",
    }
    r = client.post(f"{settings.API_V1_PREFIX}/login/access-token", data=login_data)
    assert r.status_code == status.HTTP_403_FORBIDDEN


def test_use_access_token(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    r = client.post(
        f"{settings.API_V1_PREFIX}/login/test-token",
        headers=superuser_token_headers,
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result


async def test_reset_password(db_with_user: Session, client: TestClient) -> None:

    # Test that the reset password recovery email is sent with the access token
    with patch("tubecast.core.notify.send_reset_password_email") as mock_send_email:
        r = client.post(
            f"{settings.API_V1_PREFIX}/password-recovery/test_user",
        )
    assert r.status_code == 200
    assert mock_send_email.called

    # Test that the reset password endpoint works
    token = mock_send_email.call_args[1]["token"]
    new_password = "new_password"
    r = client.post(
        f"{settings.API_V1_PREFIX}/reset-password",
        json={"token": token, "new_password": new_password},
    )
    assert r.status_code == 200

    # Test that the new password works
    login_data = {
        "username": "test_user",
        "password": new_password,
    }
    r = client.post(f"{settings.API_V1_PREFIX}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == status.HTTP_200_OK
    assert "access_token" in tokens


async def test_reset_password_with_invalid_username(
    db_with_user: Session, client: TestClient
) -> None:
    """
    Test that the reset password endpoint returns a 404 if the username is invalid
    """
    with patch("tubecast.core.notify.send_reset_password_email") as mock_send_email:
        r = client.post(
            f"{settings.API_V1_PREFIX}/password-recovery/999",
        )
    assert r.status_code == 404


async def test_reset_password_with_invalid_token(db_with_user: Session, client: TestClient) -> None:
    """
    Test that the reset password endpoint returns a 401 if the token is invalid
    """
    r = client.post(
        f"{settings.API_V1_PREFIX}/reset-password",
        json={"token": "999", "new_password": "new_password"},
    )
    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid Token"}


async def test_reset_password_with_invalid_user_id_from_token(
    db_with_user: Session, client: TestClient
) -> None:
    """
    Test that the reset password endpoint returns a 404 if the user id in the token is invalid
    """
    with patch("tubecast.core.security.decode_token") as mock_decode_token:
        mock_decode_token.return_value = "invalid_user_id"
        r = client.post(
            f"{settings.API_V1_PREFIX}/reset-password",
            json={"token": "mocked_token", "new_password": "new_password"},
        )
    assert r.status_code == 404


async def test_password_recovery_for_inactive_user(
    db_with_user: Session, client: TestClient
) -> None:
    """
    Test that the reset password endpoint returns a 400 if the user is inactive
    """
    await crud.user.update(
        db=db_with_user, username="test_user", obj_in=models.UserUpdate(is_active=False)
    )

    with patch("tubecast.core.notify.send_reset_password_email") as mock_send_email:
        r = client.post(
            f"{settings.API_V1_PREFIX}/password-recovery/test_user",
        )
    assert r.status_code == 400
    assert r.json() == {"detail": "Inactive user"}


async def test_reset_password_for_inactive_user(db_with_user: Session, client: TestClient) -> None:
    """
    Test that the reset password endpoint returns a 400 if the user is inactive
    """
    db_user = await crud.user.update(
        db=db_with_user, username="test_user", obj_in=models.UserUpdate(is_active=False)
    )

    with patch("tubecast.core.security.decode_token") as mock_decode_token:
        mock_decode_token.return_value = db_user.id
        r = client.post(
            f"{settings.API_V1_PREFIX}/reset-password",
            json={"token": "", "new_password": "new_password"},
        )
    assert r.status_code == 400
    assert r.json() == {"detail": "Inactive user"}


async def test_get_current_user_not_found(
    db_with_user: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that the current user endpoint returns a 404 if the user is not found
    """
    with patch("tubecast.core.security.decode_token") as mock_get_current_user_id:
        mock_get_current_user_id.return_value = "invalid_user_id"
        r = client.get(
            f"{settings.API_V1_PREFIX}/user/me",
            headers=normal_user_token_headers,
        )
    assert r.status_code == 404
    assert r.json() == {"detail": "User from access token not found"}


async def test_get_current_active_user_inactive_user(
    db_with_user: Session,
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    """
    Test that the current user endpoint returns a 400 if the user is inactive
    """
    db_user = await crud.user.update(
        db=db_with_user, username="test_user", obj_in=models.UserUpdate(is_active=False)
    )

    with patch("tubecast.api.deps.get_current_user_id") as mock_get_current_user_id:
        mock_get_current_user_id.return_value = db_user.id
        r = client.get(
            f"{settings.API_V1_PREFIX}/user/me",
            headers=normal_user_token_headers,
        )
    assert r.status_code == 403
    assert r.json() == {"detail": "Inactive user"}


async def test_expired_token(
    db_with_user: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that the current user endpoint returns a 401 if the token is expired
    """
    with patch("jwt.decode") as mock_decode_token:
        mock_decode_token.side_effect = jwt.ExpiredSignatureError
        r = client.get(
            f"{settings.API_V1_PREFIX}/user/me",
            headers=normal_user_token_headers,
        )
    assert r.status_code == 401
    assert r.json() == {"detail": "Expired Token"}


async def test_get_tokens_from_refresh_token(
    db_with_user: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that the refresh token endpoint returns new tokens
    """

    # Get tokens from login endpoint
    login_data = {
        "username": "test_user",
        "password": "test_password",
    }
    login_response = client.post(f"{settings.API_V1_PREFIX}/login/access-token", data=login_data)
    assert login_response.status_code == status.HTTP_200_OK
    login_tokens = login_response.json()
    refresh_token = login_tokens["refresh_token"]

    # Use the refresh token to get new tokens
    refresh_response = client.post(
        f"{settings.API_V1_PREFIX}/login/refresh-token", json=f"{refresh_token}"
    )
    assert refresh_response.status_code == 200
    refreshed_tokens = refresh_response.json()

    # Check that the new tokens are different from the old ones
    assert refreshed_tokens["refresh_token"] != login_tokens["refresh_token"]
    assert refreshed_tokens["access_token"] != login_tokens["access_token"]


async def test_get_tokens_from_refresh_token_unauthorized(
    db_with_user: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that the refresh token endpoint returns a 401 if the token is invalid
    """
    with patch("jwt.decode") as mock_decode_token:
        mock_decode_token.side_effect = jwt.InvalidTokenError
        r = client.post(
            f"{settings.API_V1_PREFIX}/login/refresh-token",
            json="invalid_token",
        )
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
    assert r.json() == {"detail": "Invalid Token"}
