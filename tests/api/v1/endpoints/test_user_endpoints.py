from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from tubecast import crud, models, settings


def test_get_users_superuser_me(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test that a superuser can retrieve their own user information.
    """
    r = client.get(f"{settings.API_V1_PREFIX}/user/me", headers=superuser_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"]
    assert current_user["username"] == settings.FIRST_SUPERUSER_USERNAME


def test_get_users_normal_user_me(
    db_with_user: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that a normal user can retrieve their own user information.
    """
    r = client.get(f"{settings.API_V1_PREFIX}/user/me", headers=normal_user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False
    assert current_user["username"] == "test_user"


@patch("tubecast.settings.EMAILS_ENABLED", True)
@patch("tubecast.settings.SMTP_PORT", 1025)
@patch("tubecast.settings.SMTP_HOST", "example.com")
@patch("tubecast.settings.EMAILS_FROM_EMAIL", "test@example.com")
async def test_create_user(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """
    Test that a superuser can create a new user.
    """
    username = "test_user2"
    data = {
        "username": username,
        "password": "test_password2",
        "email": "testemail2@example.com",
    }

    with patch("tubecast.core.notify.send_new_account_email") as mock:
        r = client.post(
            f"{settings.API_V1_PREFIX}/user/",
            headers=superuser_token_headers,
            json=data,
        )
    assert r.status_code == 200

    # Check that the user was created
    created_user = r.json()
    user = await crud.user.get(db=db, username=username)
    assert user
    assert user.username == created_user["username"]
    mock.assert_called_once_with(
        email_to=created_user["email"],
        username=created_user["username"],
        password=data["password"],
    )


def test_get_users_not_superuser(
    db_with_user: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that a normal user cannot retrieve all users.
    """
    r = client.get(f"{settings.API_V1_PREFIX}/user/2", headers=normal_user_token_headers)
    assert r.status_code == 403
    assert r.json()["detail"] == "The user doesn't have enough privileges"


async def test_get_user_not_superuser(
    db_with_user: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that a normal user cannot retrieve another user.
    """
    test_user = await crud.user.get(db=db_with_user, username=settings.FIRST_SUPERUSER_USERNAME)
    r = client.get(
        f"{settings.API_V1_PREFIX}/user/{test_user.id}", headers=normal_user_token_headers
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "The user doesn't have enough privileges"


async def test_get_existing_user(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """
    Test that a superuser can retrieve an existing user.
    """
    username = "test_user2"
    password = "test_password2"
    user_in = models.UserCreateWithPassword(
        username=username, password=password, email="test2@example.com"
    )
    user = await crud.user.create_with_password(db, obj_in=user_in)
    user_id = user.id
    r = client.get(
        f"{settings.API_V1_PREFIX}/user/{user_id}",
        headers=superuser_token_headers,
    )
    assert 200 <= r.status_code < 300
    api_user = r.json()
    existing_user = await crud.user.get(db=db, username=username)
    assert existing_user
    assert existing_user.username == api_user["username"]


async def test_get_non_existing_user(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """
    Test that a superuser cannot retrieve a non-existing user.
    """
    r = client.get(
        f"{settings.API_V1_PREFIX}/user/999",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404


async def test_create_user_existing_username(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """
    Test that a superuser cannot create a new user with an existing username.
    """
    username = "test_user"
    password = "test_password"
    email = "test@example.com"
    # user_in = models.UserCreateWithPassword(username=username, password=password, email=email)
    # await crud.user.create_with_password(db=db, obj_in=user_in)
    data = {"username": username, "password": password, "email": email}
    r = client.post(
        f"{settings.API_V1_PREFIX}/user/",
        headers=superuser_token_headers,
        json=data,
    )
    created_user = r.json()
    assert r.status_code == 409
    assert "_id" not in created_user


def test_create_user_by_normal_user(
    db_with_user: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that a normal user cannot create a new user.
    """
    username = "test_user3"
    password = "test_password3"
    email = "test3@example.com"
    data = {"username": username, "password": password, "email": email}
    r = client.post(
        f"{settings.API_V1_PREFIX}/user/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 403


def test_retrieve_users(
    db_with_user: Session, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test that a superuser can retrieve all users.
    """
    r = client.get(f"{settings.API_V1_PREFIX}/user/", headers=superuser_token_headers)
    all_users = r.json()

    assert len(all_users) == 2  # 1 superuser and 1 normal user created in conftest.py
    for item in all_users:
        assert "username" in item


def test_create_user_open(client: TestClient) -> None:
    """
    Test creating new user without the need to be logged in.
    """

    # Assert HTTP_403_FORBIDDEN if users_open_registration is False
    settings.USERS_OPEN_REGISTRATION = False
    r = client.post(
        f"{settings.API_V1_PREFIX}/register",
        json={"username": "test_user", "password": "test_password", "email": "test@example.com"},
    )
    assert r.status_code == 403

    # Assert HTTP_201_CREATED if users_open_registration is True
    settings.USERS_OPEN_REGISTRATION = True

    r = client.post(
        f"{settings.API_V1_PREFIX}/register",
        json={
            "username": "test_user9",
            "password": "test_password9",
            "email": "test9@example.com",
        },
    )
    assert r.status_code == 201

    # Assert HTTP_409_CONFLICT if username already exists
    r = client.post(
        f"{settings.API_V1_PREFIX}/register",
        json={
            "username": "test_user9",
            "password": "test_password9",
            "email": "test9@example.com",
        },
    )
    assert r.status_code == 409


async def test_update_user(
    db_with_user: Session, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test that a super user can update a user.
    """
    test_user = await crud.user.get(db=db_with_user, username="test_user")
    new_email = "newemail22@example.com"
    data = {"email": new_email, "full_name": "new name", "password": "new_password"}
    r = client.patch(
        f"{settings.API_V1_PREFIX}/user/{test_user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["email"] == new_email
    assert updated_user["full_name"] == "new name"


def test_update_user_me(
    db_with_user: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that a normal user can update their own user.
    """
    new_email = "newemail@example.com"
    data = {"email": new_email, "full_name": "new name", "password": "new_password"}
    r = client.put(
        f"{settings.API_V1_PREFIX}/user/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["email"] == new_email


async def test_delete_user(
    db_with_user: Session, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test that a super user can delete a user.
    """
    test_user = await crud.user.get(db=db_with_user, username="test_user")
    r = client.delete(
        f"{settings.API_V1_PREFIX}/user/{test_user.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 204

    r = client.get(
        f"{settings.API_V1_PREFIX}/user/{test_user.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404


async def test_delete_invalid_user(
    db_with_user: Session, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test that a super user cannot delete an invalid user.
    """
    r = client.delete(
        f"{settings.API_V1_PREFIX}/user/999",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404


async def test_authenticate_with_wrong_password(db_with_user: Session, client: TestClient) -> None:
    """
    Test that a user cannot authenticate with a wrong password.
    """
    r = client.post(
        f"{settings.API_V1_PREFIX}/login/access-token",
        data={"username": "test_user", "password": "wrong_password"},
    )
    assert r.status_code == 401
