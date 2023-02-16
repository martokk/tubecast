from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud, settings
from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1, MOCKED_YOUTUBE_SOURCE_1


async def test_read_video(
    client: TestClient,
    db_with_user: Session,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    """
    Test that a superuser can read a video.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    created_source = response.json()

    source = await crud.source.get(db=db_with_user, id=created_source["id"])
    video_0 = source.videos[0]

    # Read Source as superuser
    response = client.get(
        f"{settings.API_V1_PREFIX}/video/{video_0.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    read_video = response.json()
    assert read_video["id"] == video_0.id
    assert read_video["title"] == video_0.title
    assert read_video["description"] == video_0.description
    assert read_video["duration"] == video_0.duration
    assert read_video["thumbnail"] == video_0.thumbnail

    # Read Source as normal user is forbidden
    response = client.get(
        f"{settings.API_V1_PREFIX}/video/{video_0.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


def test_superuser_get_video_not_found(
    client: TestClient, db_with_user: Session, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test that a superuser gets a 404 when trying to read a video that does not exist.
    """
    response = client.get(
        f"{settings.API_V1_PREFIX}/video/1",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Video not found"


async def test_superuser_get_all_videos(
    db_with_user: Session,
    client: TestClient,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    """
    Test that a superuser can get all videos.
    """
    # # Create video as a normal user
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201

    # Create video as a superuser
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_RUMBLE_SOURCE_1["url"]},
    )
    assert response.status_code == 201

    # Read all Sources as superuser
    response = client.get(
        f"{settings.API_V1_PREFIX}/video/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    videos = response.json()
    assert len(videos) == 4


async def test_fetch_video(
    client: TestClient,
    db_with_user: Session,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    """
    Test that a superuser can fetch a video.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    created_source = response.json()

    source = await crud.source.get(db=db_with_user, id=created_source["id"])
    video_0 = source.videos[0]

    # Fetch Source as superuser
    response = client.put(
        f"{settings.API_V1_PREFIX}/video/{video_0.id}/fetch",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    fetched_video = response.json()
    assert fetched_video["id"] == video_0.id
    assert fetched_video["title"] == video_0.title
    assert fetched_video["description"] == video_0.description
    assert fetched_video["duration"] == video_0.duration
    assert fetched_video["thumbnail"] == video_0.thumbnail

    # Fetch Source as normal user is forbidden
    response = client.put(
        f"{settings.API_V1_PREFIX}/video/{video_0.id}/fetch",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403

    # Fetch Source that does not exist
    response = client.put(
        f"{settings.API_V1_PREFIX}/video/999/fetch",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404

    # Fetch all Sources as superuser
    response = client.put(
        f"{settings.API_V1_PREFIX}/video/fetch",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    fetched_videos = response.json()
    assert len(fetched_videos) == 2
