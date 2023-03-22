from fastapi.encoders import jsonable_encoder
from sqlmodel import Session

from app import crud, models
from app.core import security


async def test_create_user(db: Session) -> None:
    username = "test_user9"
    password = "test_password9"
    email = "test9@example.com"
    user_in = models.UserCreateWithPassword(username=username, email=email, password=password)
    user = await crud.user.create_with_password(db, obj_in=user_in)
    assert user.username == username
    assert hasattr(user, "hashed_password")


async def test_authenticate_user(db: Session, normal_user: models.User) -> None:
    """
    Test that a user can authenticate with the correct username and password.
    """
    username = "test_user"
    password = "test_password"
    authenticated_user = await crud.user.authenticate(db, username=username, password=password)
    assert authenticated_user
    assert username == authenticated_user.username


async def test_not_authenticate_user(db: Session, normal_user: models.User) -> None:
    """
    Test that a user cannot authenticate with the wrong password.
    """
    # User does not exist
    user = await crud.user.authenticate(db, username="fakeuser", password="wrongpassword")
    assert user is None

    # User exists, wrong password
    user = await crud.user.authenticate(db, username=normal_user.username, password="wrongpassword")
    assert user is None


async def test_check_if_user_is_active(db: Session, normal_user: models.User) -> None:
    """
    Test that a user is active.
    """
    user = await crud.user.get(db=db, username="test_user")
    is_active = crud.user.is_active(user)
    assert is_active is True


async def test_check_if_user_is_active_inactive(db: Session) -> None:
    """
    Test that a user is inactive.
    """
    username = "test_user9"
    password = "test_password9"
    email = "test9@example.com"
    user_in = models.UserCreateWithPassword(
        username=username, email=email, password=password, is_active=False
    )
    user = await crud.user.create_with_password(db, obj_in=user_in)
    assert crud.user.is_active(user) is False


async def test_check_if_user_is_superuser(db: Session) -> None:
    """
    Test that a user is a superuser.
    """
    username = "test_user9"
    password = "test_password9"
    email = "test9@example.com"
    user_in = models.UserCreateWithPassword(
        username=username, email=email, password=password, is_superuser=True
    )
    user = await crud.user.create_with_password(db, obj_in=user_in)
    is_superuser = crud.user.is_superuser(user_=user)
    assert is_superuser is True


async def test_check_if_user_is_superuser_normal_user(db: Session) -> None:
    """
    Test that a user is not a superuser.
    """
    username = "test_user9"
    password = "test_password9"
    email = "test9@example.com"
    user_in = models.UserCreateWithPassword(username=username, email=email, password=password)
    user = await crud.user.create_with_password(db, obj_in=user_in)
    is_superuser = crud.user.is_superuser(user_=user)
    assert is_superuser is False


async def test_get_user(db: Session) -> None:
    """
    Test that a user can be retrieved by id.
    """
    username = "test_user9"
    password = "test_password9"
    email = "test9@example.com"
    user_in = models.UserCreateWithPassword(username=username, email=email, password=password)
    user = await crud.user.create_with_password(db, obj_in=user_in)

    user_2 = await crud.user.get(db=db, id=user.id)
    assert user_2
    assert user.username == user_2.username
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


async def test_update_user(db: Session) -> None:
    """
    Test that a user can be updated.
    """
    username = "test_user9"
    password = "test_password9"
    email = "test9@example.com"
    user_in = models.UserCreateWithPassword(username=username, email=email, password=password)
    user = await crud.user.create_with_password(db, obj_in=user_in)

    new_hashed_password = security.get_password_hash(password="new_password")
    user_in_update = models.UserUpdate(hashed_password=new_hashed_password, is_superuser=True)
    await crud.user.update(db, id=user.id, obj_in=user_in_update)

    user_2 = await crud.user.get(db=db, id=user.id)
    assert user_2

    assert user.username == user_2.username
    assert user.email == user_2.email
    assert security.verify_password("new_password", user_2.hashed_password)
