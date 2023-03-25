from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Cookies
from sqlmodel import Session

from app import crud, paths
from app.models import Filter, Source, User
from app.services.fetch import FetchCanceledError
from tests.mock_objects import MOCK_FILTER_1


def test_view_filter(
    db: Session,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
    source_1: Source,
    filter_1: Filter,
) -> None:
    """
    Test view_filter.
    """

    client.cookies = normal_user_cookies
    response = client.get(f"/filter/{filter_1.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/filter/{filter_1.id}"
    assert response.template.name == "filter/view.html"  # type: ignore
    assert response.context["filter"].id == filter_1.id  # type: ignore
    assert response.context["filter"].name == filter_1.name  # type: ignore
    assert response.context["filter"].source.id == filter_1.source.id  # type: ignore
    assert response.context["filter"].ordered_by == filter_1.ordered_by  # type: ignore

    # Test filter not found
    response = client.get("/filter/invalid_id")
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == "/sources"
    assert response.context["alerts"].danger[0] == "Filter not found"  # type: ignore


def test_handle_create_filter(
    db: Session,
    client: TestClient,
    normal_user_cookies: Cookies,
    source_1: Source,
) -> None:
    """
    Test handle_create_filter.
    """
    client.cookies = normal_user_cookies
    response = client.post(
        f"/source/{source_1.id}/filter/create",
        data=MOCK_FILTER_1,
    )
    response_filter = response.context["filter"]  # type: ignore
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/filter/{response_filter.id}"
    assert response.template.name == "filter/view.html"  # type: ignore
    assert response_filter.name == MOCK_FILTER_1["name"]
    assert response_filter.source.id == source_1.id
    assert response_filter.ordered_by == MOCK_FILTER_1["ordered_by"]

    # Test missing filter name
    MOCK_FILTER_1["name"] = ""

    response = client.post(
        f"/source/{source_1.id}/filter/create",
        data=MOCK_FILTER_1,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/source/{source_1.id}"
    assert response.template.name == "source/view.html"  # type: ignore
    assert response.context["alerts"].danger[0] == "Filter name is required."  # type: ignore


def test_edit_filter(
    db: Session,
    client: TestClient,
    normal_user_cookies: Cookies,
    source_1: Source,
    filter_1: Filter,
) -> None:
    """
    Test edit_filter.
    """

    # Test edit filter
    client.cookies = normal_user_cookies
    response = client.get(
        f"/filter/{filter_1.id}/edit",  # type: ignore
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/filter/{filter_1.id}/edit"
    assert response.template.name == "filter/edit.html"  # type: ignore

    # Test invalid filter id
    response = client.get(
        f"/filter/invalid_user_id/edit",  # type: ignore
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == "/sources"
    assert response.history[0].status_code == status.HTTP_302_FOUND
    assert response.context["alerts"].danger[0] == "Filter not found"  # type: ignore


def test_handle_edit_filter(
    db: Session,
    client: TestClient,
    normal_user_cookies: Cookies,
    source_1: Source,
    filter_1: Filter,
) -> None:
    """
    Test handle_edit_filter.
    """
    MOCK_FILTER_1["name"] = "New filter name"

    # Test edit filter
    client.cookies = normal_user_cookies
    response = client.post(
        f"/filter/{filter_1.id}/edit",  # type: ignore
        data=MOCK_FILTER_1,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/filter/{filter_1.id}"
    assert response.template.name == "filter/view.html"  # type: ignore
    assert response.context["filter"].name == MOCK_FILTER_1["name"]  # type: ignore
    assert response.context["filter"].source.id == source_1.id  # type: ignore
    assert response.context["filter"].ordered_by == MOCK_FILTER_1["ordered_by"]  # type: ignore

    # Test invalid filter id
    response = client.post(
        f"/filter/invalid_user_id/edit",  # type: ignore
        data=MOCK_FILTER_1,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == "/sources"
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].danger[0] == "Filter not found"  # type: ignore


def test_delete_filter(
    db: Session,
    client: TestClient,
    normal_user_cookies: Cookies,
    source_1: Source,
    filter_1: Filter,
) -> None:
    """
    Test delete_filter.
    """

    # Test delete filter
    client.cookies = normal_user_cookies
    response = client.get(
        f"/filter/{filter_1.id}/delete",  # type: ignore
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/source/{filter_1.source.id}"
    assert response.template.name == "source/view.html"  # type: ignore

    # Test invalid filter id
    response = client.get(
        f"/filter/invalid_user_id/delete",  # type: ignore
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == "/sources"
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].danger[0] == "Filter not found"  # type: ignore


def test_fetch_filter_page(
    db: Session,
    client: TestClient,
    normal_user_cookies: Cookies,
    superuser_cookies: Cookies,
    filter_1: Filter,
) -> None:
    """
    Test fetching a filter.
    """

    # Attempt to fetch source as normal user
    client.cookies = normal_user_cookies
    response = client.get(
        f"/filter/{filter_1.id}/fetch",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].danger[0] == "You are not authorized to do that"  # type: ignore
    assert response.url.path == f"/filter/{filter_1.id}"

    # Fetch source as superuser
    with patch("app.services.fetch.fetch_source", return_value=None):
        client.cookies = superuser_cookies
        response = client.get(
            f"/filter/{filter_1.id}/fetch",
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].success[0] == f"Filter '{filter_1.name}' was fetched."  # type: ignore
    assert response.url.path == f"/filter/{filter_1.id}"

    # Fetch source as superuser with not found source
    with patch("app.services.fetch.fetch_source", return_value=None):
        client.cookies = superuser_cookies
        response = client.get(
            f"/filter/wrongs_source_id/fetch",
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].danger[0] == "Filter not found"  # type: ignore
    assert response.url.path == f"/sources"

    # Fetch Source was canceled
    with patch("app.views.pages.filters.fetch_source", return_value=None) as mocked_fetch_source:
        mocked_fetch_source.side_effect = FetchCanceledError
        client.cookies = superuser_cookies
        response = client.get(
            f"/filter/{filter_1.id}/fetch",
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert (
        response.context["alerts"].danger[0] == f"Fetch of filter '{filter_1.name}' was cancelled."  # type: ignore
    )
    assert response.url.path == f"/filter/{filter_1.id}"


def test_get_filter_rss_feed(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    source_1: Source,
    filter_1: Filter,
) -> None:
    """
    Test that a valid rss file is returned.
    """
    # Delete file if it exists
    file = paths.FEEDS_PATH / f"{filter_1.id}.rss"
    file.unlink(missing_ok=True)

    response = client.get(
        f"/filter/{filter_1.id}/feed",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert "<rss" in str(response.content)
    assert "/rss>" in str(response.content)


def test_delete_filter_rss_feed(
    client: TestClient,
    db: Session,
    normal_user_cookies: Cookies,
    superuser_cookies: Cookies,
    normal_user: User,
    source_1: Source,
    filter_1: Filter,
) -> None:
    """
    Test that a valid rss file is returned.
    """
    # Test DeleteError
    with patch("app.crud.filter.remove", side_effect=crud.DeleteError):
        response = client.get(
            f"/filter/{filter_1.id}/delete",
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.context["alerts"].danger[0] == "Error deleting filter"  # type: ignore
    assert response.url.path == f"/filter/{filter_1.id}"

    # Test Delete
    client.cookies = normal_user_cookies
    response = client.get(
        f"/filter/{filter_1.id}/delete",
    )
    assert response.status_code == 200
    assert response.url.path == f"/source/{filter_1.source.id}"
    assert response.template.name == "source/view.html"  # type: ignore
