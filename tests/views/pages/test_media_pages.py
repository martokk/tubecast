from unittest.mock import patch

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
    with patch("app.views.pages.media.RedirectResponse") as mock_redirect:
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
    with patch("app.views.pages.media.reverse_proxy") as mock_reverse_proxy:
        mock_reverse_proxy.return_value = Response(content=None, status_code=200)
        response = client.get(source_video_0_url)
        assert response.status_code == 200


async def test_html_view_users_sources_no_media_url(
    db_with_user: Session,
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
    created_source = response.json()

    # Get source videos
    videos = await crud.video.get_multi(db=db_with_user, source_id=created_source["id"])
    first_video = videos[0]

    # Update source media_url to None
    obj_in = models.VideoUpdate(media_url=None)
    db_video = await crud.video.update(
        db=db_with_user, obj_in=obj_in, id=first_video.id, exclude_none=False
    )

    # Handle Media
    response = client.get(
        f"/media/{db_video.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 202
    assert response.json() == {
        "detail": f"The server has not yet retrieved a media_url from yt-dlp. video_id='{db_video.id}'",
    }
