from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Cookies
from sqlmodel import Session

from app import crud, models


def test_view_video(
    source_1_w_videos: models.Source,
    client: TestClient,
    normal_user_cookies: Cookies,
) -> None:
    """Test the view video page."""
    test_video = source_1_w_videos.videos[0]

    client.cookies = normal_user_cookies
    response = client.get(f"/video/{test_video.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/video/{test_video.id}"

    # Test not found
    client.cookies = normal_user_cookies
    response = client.get(f"/video/invalid_id")
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/sources"
    assert response.context["alerts"].danger[0] == "Video not found"  # type: ignore


def test_fetch_video_page(
    source_1_w_videos: models.Source,
    client: TestClient,
    normal_user_cookies: Cookies,
    superuser_cookies: Cookies,
) -> None:
    """Test the fetch video page."""
    test_video = source_1_w_videos.videos[0]

    # Test normal user
    client.cookies = normal_user_cookies
    response = client.get(f"/video/{test_video.id}/fetch")
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/video/{test_video.id}"
    assert response.context["alerts"].danger[0] == "You are not authorized to do that"  # type: ignore

    # Test not found
    client.cookies = superuser_cookies
    response = client.get(f"/video/invalid_id/fetch")
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/sources"
    assert response.context["alerts"].danger[0] == f"Video not found"  # type: ignore

    # Test superuser fetch video
    with patch("app.views.pages.videos.fetch_video") as mock_fetch_video:
        client.cookies = superuser_cookies
        response = client.get(f"/video/{test_video.id}/fetch")
        assert mock_fetch_video.called
        assert response.status_code == status.HTTP_200_OK
        assert response.url.path == f"/video/{test_video.id}"
        assert response.context["alerts"].success[0] == f"Video '{test_video.title}' was fetched."  # type: ignore
