from unittest.mock import patch

from fastapi import status
from fastapi.responses import RedirectResponse, Response
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud, models, settings
from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1, MOCKED_YOUTUBE_SOURCE_1


async def test_handle_media_404(client: TestClient) -> None:
    response = client.get("/media/wrong-id")
    assert response.status_code == 404


async def test_handle_redirect_media(
    db: Session, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # Create a source
    response = client.post(
        "/api/v1/source",
        headers=superuser_token_headers,
        json={"url": MOCKED_RUMBLE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    created_source = response.json()

    # Get source videos
    response = client.get(
        f"/api/v1/source/{created_source['id']}/videos", headers=superuser_token_headers
    )
    assert response.status_code == 200
    source_videos = response.json()

    # Handle media
    source_video_0_url = source_videos[0]["feed_media_url"]
    with patch("app.services.media.RedirectResponse") as mock_redirect:
        mock_redirect.return_value = RedirectResponse(url="http://example.com")
        response = client.get(source_video_0_url)
        assert response.status_code == 200


async def test_handle_reverse_proxy_media(
    db: Session, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # Create a source
    response = client.post(
        "/api/v1/source",
        headers=superuser_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    created_source = response.json()

    # Get source videos
    response = client.get(
        f"/api/v1/source/{created_source['id']}/videos", headers=superuser_token_headers
    )
    assert response.status_code == 200
    source_videos = response.json()

    # Handle media
    source_video_0_url = source_videos[0]["feed_media_url"]
    with patch("app.services.media.reverse_proxy") as mock_reverse_proxy:
        mock_reverse_proxy.return_value = Response(content=None, status_code=200)
        response = client.get(source_video_0_url)
        assert response.status_code == 200


async def test_html_view_users_sources_no_media_url(
    db: Session,
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    """
    Test that the html_view_users_sources function returns a response with the correct status code.
    """
    # Create sources for normal test user
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_RUMBLE_SOURCE_1["url"]},
    )
    assert response.status_code == 201


async def test_handle_media_video_no_media_url(
    db: Session,
    source_1_w_videos: models.Source,
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    """
    Test that the handle_media function returns a response with the correct status code.
    """
    test_video = source_1_w_videos.videos[0]
    test_video.media_url = None

    with patch("app.crud.video.VideoCRUD.get") as mock_get:
        mock_get.return_value = test_video

        with patch("app.services.media.fetch_video") as mock_fetch_video:
            mock_fetch_video.return_value = test_video

            response = client.get(f"/media/{test_video.id}")

    mock_get.assert_called_once()
    mock_fetch_video.assert_called_once()

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert "The server has not able to fetch a media_url from yt-dlp." in response.text
