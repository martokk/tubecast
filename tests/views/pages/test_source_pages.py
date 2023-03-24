from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Cookies
from sqlmodel import Session

from app import crud, models
from app.services.source import FetchCancelledError
from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1, MOCKED_SOURCES, MOCKED_YOUTUBE_SOURCE_1


@pytest.fixture(name="sources")
async def fixture_sources(
    db: Session, normal_user: models.User, superuser: models.User
) -> list[models.Source]:
    """
    Create an source for testing.
    """
    # Create 1 as a superuser
    sources = []
    sources.append(
        await crud.source.create_source_from_url(
            db=db, url=MOCKED_SOURCES[0]["url"], user_id=superuser.id
        )
    )

    # Create 2 as a normal user
    for mocked_source in [MOCKED_SOURCES[1], MOCKED_SOURCES[2]]:
        sources.append(
            await crud.source.create_source_from_url(
                db=db, url=mocked_source["url"], user_id=normal_user.id
            )
        )
    return sources


def test_handle_create_source(
    db: Session,  # pylint: disable=unused-argument
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
    assert response.url.path == f"/source/{MOCKED_RUMBLE_SOURCE_1['id']}"
    assert response.template.name == "source/view.html"  # type: ignore


@pytest.mark.filterwarnings("ignore::sqlalchemy.exc.SAWarning")
def test_create_duplicate_source(
    db: Session,  # pylint: disable=unused-argument
    source_1: models.Source,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
) -> None:  # pytest:
    """
    Test a duplicate source cannot be created.
    """
    # Try to create a duplicate source
    client.cookies = normal_user_cookies
    response = client.post(
        "/sources/create",
        data=MOCKED_RUMBLE_SOURCE_1,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/sources"
    assert response.template.name == "source/list.html"  # type: ignore
    assert response.context["alerts"].danger[0] == f"Source '{source_1.name}' already exists"  # type: ignore


def test_read_source(
    db: Session,  # pylint: disable=unused-argument
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
    assert response.context["source"].id == source_1.id  # type: ignore

    # Test that a source not found error is returned.
    response = client.get("/source/8675309")
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == "/sources"


def test_get_source_forbidden(
    db: Session,  # pylint: disable=unused-argument
    source_1: models.Source,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
    superuser_cookies: Cookies,
) -> None:  # sourcery skip: extract-duplicate-method
    """
    Test that a forbidden error is returned when a user tries to read an source
    """
    # Create source as superuser
    client.cookies = superuser_cookies
    response = client.post(
        "/sources/create",
        data=MOCKED_YOUTUBE_SOURCE_1,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/source/{MOCKED_YOUTUBE_SOURCE_1['id']}"

    # Read the source as normal user
    client.cookies = normal_user_cookies
    response = client.get(
        f"/source/{MOCKED_YOUTUBE_SOURCE_1['id']}",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.template.name == "source/list.html"  # type: ignore
    assert response.context["alerts"].danger[0] == "You do not have access to this source"  # type: ignore

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
    db: Session,  # pylint: disable=unused-argument
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
    db: Session,  # pylint: disable=unused-argument
    source_1: models.Source,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
    superuser_cookies: Cookies,
) -> None:
    """
    Test that the edit source page is returned.
    """

    # Test that normal user can NOT edit source
    client.cookies = normal_user_cookies
    response = client.get(
        f"/source/{source_1.id}/edit",  # type: ignore
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test that superuser CAN edit source
    client.cookies = superuser_cookies
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
    db: Session,  # pylint: disable=unused-argument
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
    assert response.template.name == "source/view.html"  # type: ignore

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
    assert response.context["alerts"].danger[0] == "Source 'invalid_user_id' not found"  # type: ignore
    assert response.url.path == "/sources"


def test_edit_source_reverse_import_order(
    mocker: MagicMock,
    db: Session,  # pylint: disable=unused-argument
    client: TestClient,
    source_1: models.Source,
    normal_user_cookies: Cookies,
) -> None:
    """
    Test that a user can update an source.
    """
    client.cookies = normal_user_cookies

    # Update the source
    MOCKED_UPDATE = MOCKED_SOURCES[1].copy()
    MOCKED_UPDATE["reverse_import_order"] = True

    with patch("fastapi.BackgroundTasks.add_task", return_value=None) as mocked_task:
        response = client.post(
            f"/source/{source_1.id}/edit",  # type: ignore
            data=MOCKED_UPDATE,
        )
        assert mocked_task.call_count == 1
        assert response.status_code == status.HTTP_200_OK
        assert response.template.name == "source/view.html"  # type: ignore


def test_delete_source(
    db: Session,  # pylint: disable=unused-argument
    source_1: models.Source,
    client: TestClient,
    normal_user_cookies: Cookies,
) -> None:
    """
    Test that a user can delete an source.
    """
    client.cookies = normal_user_cookies

    # Test DeleteError raised and handled
    with patch("app.crud.source.remove", side_effect=crud.DeleteError):
        response = client.get(
            f"/source/{source_1.id}/delete",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
        assert response.context["alerts"].danger[0] == "Error deleting source"  # type: ignore

    # Test Delete the source
    response = client.get(
        f"/source/{source_1.id}/delete",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.url.path == "/sources"

    # Validate source is deleted
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


def test_list_all_sources(
    db: Session,  # pylint: disable=unused-argument
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


def test_fetch_source(
    db: Session,  # pylint: disable=unused-argument
    source_1: models.Source,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
    superuser_cookies: Cookies,
) -> None:
    """
    Test fetching a source.
    """

    # Attempt to fetch source as normal user
    client.cookies = normal_user_cookies
    response = client.get(
        f"/source/{source_1.id}/fetch",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].danger[0] == "You are not authorized to do that"  # type: ignore
    assert response.url.path == f"/source/{source_1.id}"

    # Fetch source as superuser
    with patch("app.services.source.fetch_source", return_value=None):
        client.cookies = superuser_cookies
        response = client.get(
            f"/source/{source_1.id}/fetch",
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].success[0] == f"Source '{source_1.name}' was fetched."  # type: ignore
    assert response.url.path == f"/source/{source_1.id}"

    # Fetch source as superuser with not found source
    with patch("app.services.source.fetch_source", return_value=None):
        client.cookies = superuser_cookies
        response = client.get(
            f"/source/wrongs_source_id/fetch",
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].danger[0] == "Source not found"  # type: ignore
    assert response.url.path == f"/sources"

    # Fetch Source was canceled
    with patch("app.views.pages.sources.fetch_source", return_value=None) as mocked_fetch_source:
        mocked_fetch_source.side_effect = FetchCancelledError
        client.cookies = superuser_cookies
        response = client.get(
            f"/source/{source_1.id}/fetch",
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert (
        response.context["alerts"].danger[0] == f"Fetch of source '{source_1.name}' was cancelled."  # type: ignore
    )
    assert response.url.path == f"/source/{source_1.id}"


def test_fetch_all_sources(
    db: Session,  # pylint: disable=unused-argument
    source_1: models.Source,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
    superuser_cookies: Cookies,
) -> None:
    """
    Test fetching all sources.
    """

    # Attempt to fetch all sources as normal user
    client.cookies = normal_user_cookies
    response = client.get(
        f"/sources/fetch",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].danger[0] == "You are not authorized to do that"  # type: ignore
    assert response.url.path == f"/sources"

    # Fetch all sources as superuser
    with patch("fastapi.BackgroundTasks.add_task", return_value=None) as mocked_task:
        client.cookies = superuser_cookies
        response = client.get(
            f"/sources/fetch",
        )
        assert mocked_task.call_count == 1
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].success[0] == "Fetching all sources..."  # type: ignore
    assert response.url.path == f"/sources"


def test_get_source_rss_feed(
    db: Session,  # pylint: disable=unused-argument
    source_1: models.Source,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
    superuser_cookies: Cookies,
) -> None:
    """
    Test getting a source's RSS feed.
    """
    with patch("app.views.pages.sources.build_rss_file", return_value=None) as mocked:
        response = client.get(
            f"/source/{source_1.id}/feed",
        )
        assert mocked.call_count == 1
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert f"RSS file ({source_1.id}.rss) does not exist" in response.text
    assert response.url.path == f"/source/{source_1.id}/feed"

    # Get source's RSS feed as superuser with not found source
    with patch("app.views.pages.sources.build_rss_file", return_value=None) as mocked:
        client.cookies = superuser_cookies
        response = client.get(
            f"/source/wrongs_source_id/feed",
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Source 'wrongs_source_id' not found."
