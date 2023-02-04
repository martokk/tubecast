from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Cookies
from sqlmodel import Session

from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1, MOCKED_SOURCES
from tubecast import crud, models, settings


@pytest.fixture(name="source_1")
async def fixture_source_1(db_with_user: Session) -> models.Source:
    """
    Create an source for testing.
    """
    user = await crud.user.get(db=db_with_user, username="test_user")
    return await crud.source.create_source_from_url(
        db=db_with_user, url=MOCKED_RUMBLE_SOURCE_1["url"], user_id=user.id
    )


@pytest.fixture(name="sources")
async def fixture_sources(db_with_user: Session) -> list[models.Source]:
    """
    Create an source for testing.
    """
    # Create 1 as a superuser
    user = await crud.user.get(db=db_with_user, username=settings.FIRST_SUPERUSER_USERNAME)
    sources = []
    sources.append(
        await crud.source.create_source_from_url(
            db=db_with_user, url=MOCKED_SOURCES[0]["url"], user_id=user.id
        )
    )

    # Create 2 as a normal user
    user = await crud.user.get(db=db_with_user, username="test_user")
    for mocked_source in [MOCKED_SOURCES[1], MOCKED_SOURCES[2]]:
        sources.append(
            await crud.source.create_source_from_url(
                db=db_with_user, url=mocked_source["url"], user_id=user.id
            )
        )
    return sources


def test_create_source_page(
    db_with_user: Session,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
) -> None:
    """
    Test that the create source page is returned.
    """
    client.cookies = normal_user_cookies
    response = client.get("/sources/create")
    assert response.status_code == status.HTTP_200_OK
    assert response.template.name == "source/create.html"  # type: ignore


def test_handle_create_source(
    db_with_user: Session,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
) -> None:
    """
    Test that a user can create a new source.
    """
    client.cookies = normal_user_cookies
    response = client.post(
        "/sources/create",
        data=MOCKED_RUMBLE_SOURCE_1,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.template.name == "source/list.html"  # type: ignore


@pytest.mark.filterwarnings("ignore::sqlalchemy.exc.SAWarning")
def test_create_duplicate_source(
    db_with_user: Session,  # pylint: disable=unused-argument
    source_1: models.Source,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
) -> None:  # pytest:
    """
    Test a duplicate source cannot be created.
    """
    # Try to create a duplicate source
    response = client.post(
        "/sources/create",
        data=MOCKED_RUMBLE_SOURCE_1,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.template.name == "source/create.html"  # type: ignore
    assert response.context["alerts"].danger[0] == "Source already exists"  # type: ignore


def test_read_source(
    db_with_user: Session,  # pylint: disable=unused-argument
    source_1: models.Source,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
) -> None:
    """
    Test that a user can read an source.
    """
    # Read the source
    response = client.get(
        f"/source/{source_1.id}",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.template.name == "source/view.html"  # type: ignore


def test_get_source_not_found(
    db_with_user: Session,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
) -> None:
    """
    Test that a source not found error is returned.
    """
    client.cookies = normal_user_cookies

    # Read the source
    response = client.get("/source/8675309")
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == "/sources"


def test_get_source_forbidden(
    db_with_user: Session,  # pylint: disable=unused-argument
    source_1: models.Source,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
) -> None:  # sourcery skip: extract-duplicate-method
    """
    Test that a forbidden error is returned when a user tries to read an source
    """
    client.cookies = normal_user_cookies

    # Read the source
    response = client.get(
        f"/source/{source_1.id}",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.template.name == "source/view.html"  # type: ignore

    # Logout
    response = client.get(
        "/logout",
    )
    assert response.status_code == status.HTTP_200_OK

    # Attempt Read the source
    response = client.get(
        f"/source/{source_1.id}",  # type: ignore
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_normal_user_get_all_sources(
    db_with_user: Session,  # pylint: disable=unused-argument
    sources: list[models.Source],  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
    superuser_cookies: Cookies,
) -> None:  # sourcery skip: extract-duplicate-method
    """
    Test that a normal user can get all their own sources.
    """

    # List all sources as normal user
    client.cookies = normal_user_cookies
    response = client.get(
        "/sources",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.template.name == "source/list.html"  # type: ignore

    # Assert only 2 sources are returned (not the superuser's source)
    assert len(response.context["sources"]) == 2  # type: ignore


def test_edit_source_page(
    db_with_user: Session,  # pylint: disable=unused-argument
    source_1: models.Source,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
) -> None:
    """
    Test that the edit source page is returned.
    """
    client.cookies = normal_user_cookies
    response = client.get(
        f"/source/{source_1.id}/edit",  # type: ignore
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.template.name == "source/edit.html"  # type: ignore

    # Test invalid source id
    response = client.get(
        f"/source/invalid_user_id/edit",  # type: ignore
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_302_FOUND
    assert response.context["alerts"].danger[0] == "Source not found"  # type: ignore
    assert response.url.path == "/sources"


def test_update_source(
    db_with_user: Session,  # pylint: disable=unused-argument
    client: TestClient,
    source_1: models.Source,
    normal_user_cookies: Cookies,
) -> None:
    """
    Test that a user can update an source.
    """
    client.cookies = normal_user_cookies

    # Update the source
    response = client.post(
        f"/source/{source_1.id}/edit",  # type: ignore
        data=MOCKED_SOURCES[1],
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.template.name == "source/edit.html"  # type: ignore

    # View the source
    response = client.get(
        f"/source/{source_1.id}",  # type: ignore
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.template.name == "source/view.html"  # type: ignore
    assert response.context["source"].name == MOCKED_SOURCES[1]["name"]  # type: ignore
    assert response.context["source"].description == MOCKED_SOURCES[1]["description"]  # type: ignore
    assert response.context["source"].url == MOCKED_SOURCES[1]["url"]  # type: ignore

    # Test invalid source id
    response = client.post(
        f"/source/invalid_user_id/edit",  # type: ignore
        data=MOCKED_SOURCES[1],
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].danger[0] == "Source not found"  # type: ignore
    assert response.url.path == "/sources"


def test_delete_source(
    db_with_user: Session,  # pylint: disable=unused-argument
    source_1: models.Source,
    client: TestClient,
    normal_user_cookies: Cookies,
) -> None:
    """
    Test that a user can delete an source.
    """
    client.cookies = normal_user_cookies

    # Delete the source
    response = client.get(
        f"/source/{source_1.id}/delete",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.url.path == "/sources"

    # View the source
    response = client.get(
        f"/source/{source_1.id}",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.context["alerts"].danger == ["Source not found"]  # type: ignore

    # Test invalid source id
    response = client.get(
        f"/source/invalid_user_id/delete",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].danger[0] == "Source not found"  # type: ignore
    assert response.url.path == "/sources"

    # Test DeleteError
    with patch("tubecast.crud.source.remove", side_effect=crud.DeleteError):
        response = client.get(
            f"/source/123/delete",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
        assert response.context["alerts"].danger[0] == "Error deleting source"  # type: ignore


def test_list_all_sources(
    db_with_user: Session,  # pylint: disable=unused-argument
    sources: list[models.Source],  # pylint: disable=unused-argument
    client: TestClient,
    superuser_cookies: Cookies,
) -> None:  # sourcery skip: extract-duplicate-method
    """
    Test that a superuser can get all sources.
    """

    # List all sources as superuser
    client.cookies = superuser_cookies
    response = client.get(
        "/sources/all",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.template.name == "source/list.html"  # type: ignore

    # Assert all 3 sources are returned
    assert len(response.context["sources"]) == 3  # type: ignore
