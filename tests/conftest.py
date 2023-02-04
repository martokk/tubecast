from typing import Any

from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import sqlalchemy as sa
from fastapi import Request, Response
from fastapi.testclient import TestClient
from httpx import Cookies
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine

from tests.mock_objects import get_mocked_source_info_dict, get_mocked_video_info_dict
from tubecast import crud, models, settings
from tubecast.api import deps as api_deps
from tubecast.core import security
from tubecast.core.app import app
from tubecast.db.init_db import init_initial_data
from tubecast.views import deps as views_deps

# Set up the database
db_url = "sqlite:///:memory:"
engine = create_engine(
    db_url,
    echo=False,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)
SQLModel.metadata.drop_all(bind=engine)
SQLModel.metadata.create_all(bind=engine)


# These two event listeners are only needed for sqlite for proper
# SAVEPOINT / nested transaction support. Other databases like postgres
# don't need them.
# From: https://docs.sqlalchemy.org/en/14/dialects/sqlite.html
# #serializable-isolation-savepoints-transactional-ddl
@sa.event.listens_for(engine, "connect")  # type: ignore
def do_connect(dbapi_connection: Any, connection_record: Any) -> None:
    # disable pysqlite's emitting of the BEGIN statement entirely.
    # also stops it from emitting COMMIT before any DDL.
    dbapi_connection.isolation_level = None


@sa.event.listens_for(engine, "begin")  # type: ignore
def do_begin(conn: Any) -> None:
    # emit our own BEGIN
    conn.exec_driver_sql("BEGIN")


@pytest.fixture(name="init")
def fixture_init(mocker: MagicMock, tmp_path: Path) -> None:  # pylint: disable=unused-argument
    mocker.patch("tubecast.paths.FEEDS_PATH", return_value=tmp_path)
    mocker.patch("tubecast.paths.LOG_FILE", return_value=tmp_path / "test.log")
    mocker.patch("tubecast.services.feed.build_rss_file", None)


@pytest.fixture(name="db")
async def fixture_db(
    init: Any, tmp_path: Path, mocker: MagicMock  # pylint: disable=unused-argument
) -> AsyncGenerator[Session, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Begin a nested transaction (using SAVEPOINT).
    nested = connection.begin_nested()
    await init_initial_data(db=session)

    # If the application code calls session.commit, it will end the nested
    # transaction. Need to start a new one when that happens.
    @sa.event.listens_for(session, "after_transaction_end")  # type: ignore
    def end_savepoint(  # type: ignore
        session: Any, transaction: Any  # pylint: disable=unused-argument
    ) -> None:
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    mocker.patch("tubecast.services.feed.FEEDS_PATH", tmp_path)
    with (
        patch(
            "tubecast.services.source.get_info_dict",
            get_mocked_source_info_dict,
        ),
        patch(
            "tubecast.services.video.get_info_dict",
            get_mocked_video_info_dict,
        ),
    ):
        yield session

    # Rollback the overall transaction, restoring the state before the test ran.
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="client")
async def fixture_client(db: Session) -> AsyncGenerator[TestClient, None]:
    """
    Fixture that creates a test client with the database session override.

    Args:
        db (Session): database session.

    Yields:
        TestClient: test client with database session override.
    """

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[api_deps.get_db] = override_get_db
    app.dependency_overrides[views_deps.get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[api_deps.get_db]
    del app.dependency_overrides[views_deps.get_db]


@pytest.fixture(name="db_with_user")
async def fixture_db_with_user(db: Session) -> Session:
    """
    Fixture that creates an example user in the test database.

    Args:
        db (Session): database session.

    Returns:
        Session: database session with example user.
    """
    user_hashed_password = security.get_password_hash("test_password")
    user_create = models.UserCreate(
        username="test_user", email="test@example.com", hashed_password=user_hashed_password
    )
    await crud.user.create(obj_in=user_create, db=db)
    return db


@pytest.fixture(name="superuser_token_headers")
def superuser_token_headers(db_with_user: Session, client: TestClient) -> dict[str, str]:
    """
    Fixture that returns the headers for a superuser.

    Args:
        db_with_user (Session): database session.
        client (TestClient): test client.

    Returns:
        dict[str, str]: headers for a superuser.
    """
    login_data = {
        "username": settings.FIRST_SUPERUSER_USERNAME,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_PREFIX}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    return {"Authorization": f"Bearer {a_token}"}


@pytest.fixture(name="normal_user_token_headers")
def normal_user_token_headers(client: TestClient) -> dict[str, str]:
    """
    Fixture that returns the headers for a normal user.

    Args:
        client (TestClient): test client.

    Returns:
        dict[str, str]: headers for a normal user.
    """
    login_data = {
        "username": "test_user",
        "password": "test_password",
    }
    r = client.post(f"{settings.API_V1_PREFIX}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    return {"Authorization": f"Bearer {a_token}"}


@pytest.fixture(name="test_request")
def fixture_request() -> Request:
    """
    Fixture that returns a request object.

    Returns:
        Request: request object.
    """
    return Request(scope={"type": "http", "method": "GET", "path": "/"})


@pytest.fixture(name="normal_user_cookies")
def fixture_normal_user_cookies(
    db_with_user: Session, client: TestClient  # pylint: disable=unused-argument
) -> Cookies:
    """
    Fixture that returns the cookie_data for a normal user.

    Args:
        db_with_user (Session): database session.
        client (TestClient): test client.

    Returns:
        Cookies: cookie_data for a normal user.
    """
    form_data = {"username": "test_user", "password": "test_password"}

    with patch("tubecast.views.pages.login.RedirectResponse") as mock:
        mock.return_value = Response(status_code=302)
        response = client.post("/login", data=form_data)
        print(response.cookies)
        return response.cookies


@pytest.fixture(name="superuser_cookies")
def fixture_superuser_cookies(
    db_with_user: Session, client: TestClient  # pylint: disable=unused-argument
) -> Cookies:
    """
    Fixture that returns the cookie_data for a normal user.

    Args:
        db_with_user (Session): database session.
        client (TestClient): test client.

    Returns:
        Cookies: cookie_data for a normal user.
    """
    form_data = {
        "username": settings.FIRST_SUPERUSER_USERNAME,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }

    with patch("tubecast.views.pages.login.RedirectResponse") as mock:
        mock.return_value = Response(status_code=302)
        response = client.post("/login", data=form_data)
        print(response.cookies)
        return response.cookies
