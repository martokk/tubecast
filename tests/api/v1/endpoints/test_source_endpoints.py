from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1, MOCKED_YOUTUBE_SOURCE_1
from tubecast import settings


def test_create_source_from_url(
    client: TestClient,
    db_with_user: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    """
    Test that a normal user can create a source from a URL.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    source = response.json()
    assert source["created_by"] == MOCKED_YOUTUBE_SOURCE_1["created_by"]
    assert source["url"] == MOCKED_YOUTUBE_SOURCE_1["url"]
    assert source["name"] == MOCKED_YOUTUBE_SOURCE_1["name"]
    assert source["logo"] == MOCKED_YOUTUBE_SOURCE_1["logo"]
    assert source["ordered_by"] == MOCKED_YOUTUBE_SOURCE_1["ordered_by"]
    assert source["feed_url"] == MOCKED_YOUTUBE_SOURCE_1["feed_url"]
    assert source["handler"] == MOCKED_YOUTUBE_SOURCE_1["handler"]
    assert source["author"] == MOCKED_YOUTUBE_SOURCE_1["author"]
    assert source["description"] == MOCKED_YOUTUBE_SOURCE_1["description"]
    assert source["extractor"] == MOCKED_YOUTUBE_SOURCE_1["extractor"]
    assert source["created_at"] is not None
    assert source["updated_at"] is not None


def test_create_duplicate_source(
    client: TestClient, db_with_user: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test a normal user can not create a duplicate source.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201

    # Try to create a duplicate source
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 200
    duplicate = response.json()
    assert duplicate["detail"] == "Source already exists"


def test_read_source(
    client: TestClient, db_with_user: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that a normal user can read a source.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    created_source = response.json()

    # Read Source
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/{created_source['id']}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    read_source = response.json()

    assert read_source["created_by"] == MOCKED_YOUTUBE_SOURCE_1["created_by"]
    assert read_source["url"] == MOCKED_YOUTUBE_SOURCE_1["url"]
    assert read_source["name"] == MOCKED_YOUTUBE_SOURCE_1["name"]
    assert read_source["logo"] == MOCKED_YOUTUBE_SOURCE_1["logo"]
    assert read_source["ordered_by"] == MOCKED_YOUTUBE_SOURCE_1["ordered_by"]
    assert read_source["feed_url"] == MOCKED_YOUTUBE_SOURCE_1["feed_url"]
    assert read_source["handler"] == MOCKED_YOUTUBE_SOURCE_1["handler"]
    assert read_source["author"] == MOCKED_YOUTUBE_SOURCE_1["author"]
    assert read_source["description"] == MOCKED_YOUTUBE_SOURCE_1["description"]
    assert read_source["extractor"] == MOCKED_YOUTUBE_SOURCE_1["extractor"]
    assert read_source["created_by"] == MOCKED_YOUTUBE_SOURCE_1["created_by"]
    assert read_source["created_at"] is not None
    assert read_source["updated_at"] is not None


def test_normal_user_get_source_not_found(
    client: TestClient, db_with_user: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that a normal user gets a 403 when trying to read a source that does not exist.
    """
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/1",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_superuser_get_source_not_found(
    client: TestClient, db_with_user: Session, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test that a superuser gets a 404 when trying to read a source that does not exist.
    """
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/1",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Source not found"


def test_get_source_forbidden(
    db_with_user: Session,
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    """
    Test that a normal user can not get a source created by another user.
    """
    # Create source as superuser
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    created_source = response.json()

    # Read Source as normal user
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/{created_source['id']}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


async def test_superuser_get_all_sources(
    db_with_user: Session,
    client: TestClient,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    """
    Test that a superuser can get all sources.
    """
    # # Create source as a normal user
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201

    # Create source as a superuser
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_RUMBLE_SOURCE_1["url"]},
    )
    assert response.status_code == 201

    # Read all Sources as superuser
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) == 2


def test_normal_user_get_all_own_sources(
    db_with_user: Session,
    client: TestClient,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    """
    Test that a normal user can get all sources created by them.
    """
    # Create source as a normal user
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201

    # Create source as a superuser
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_RUMBLE_SOURCE_1["url"]},
    )
    assert response.status_code == 201

    # Read all Sources created by normal user
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) == 1


def test_update_source(
    db_with_user: Session,
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    """
    Test that a superuser can update an source.
    """
    # Create source as a normal user
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    created_source = response.json()

    # Update Source as superuser
    update_data = {"name": "Updated Title"}
    response = client.patch(
        f"{settings.API_V1_PREFIX}/source/{created_source['id']}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response.status_code == 200
    updated_source = response.json()
    assert updated_source["name"] == update_data["name"]

    # Update wrong source
    response = client.patch(
        f"{settings.API_V1_PREFIX}/source/99999",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response.status_code == 404


def test_update_source_forbidden(
    db_with_user: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that a forbidden error is returned.
    """
    response = client.patch(
        f"{settings.API_V1_PREFIX}/source/5kwf8hFn",
        headers=normal_user_token_headers,
        json=MOCKED_YOUTUBE_SOURCE_1,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_superuser_delete_source(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test that a superuser can delete an source.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=MOCKED_YOUTUBE_SOURCE_1,
    )
    assert response.status_code == 201
    created_source = response.json()

    # Delete Source
    response = client.delete(
        f"{settings.API_V1_PREFIX}/source/{created_source['id']}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 204

    # Delete wrong source
    response = client.delete(
        f"{settings.API_V1_PREFIX}/source/99999",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_normal_user_get_videos_from_source_forbidden(
    db_with_user: Session,
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    """
    Test that a normal user cannot get videos from an source that they didn't create.
    """
    # Create source as a superuser
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    created_source = response.json()

    # Get videos from source
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/{created_source['id']}/videos",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_normal_user_delete_source_forbidden(
    db_with_user: Session,
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    """
    Test that a normal user cannot get videos from an source that they didn't create.
    """
    # Create source as a superuser
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    created_source = response.json()

    # Attempt to delete source as normal user
    response = client.delete(
        f"{settings.API_V1_PREFIX}/source/{created_source['id']}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"

    # Attempt to delete a source that doesn't exist
    response = client.delete(
        f"{settings.API_V1_PREFIX}/source/99999999",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_fetch_source(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """
    Test that a superuser can fetch an source.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    created_source = response.json()

    # Fetch Source
    with patch("tubecast.crud.source.fetch_source") as mocked_fetch_source:
        mocked_fetch_source.return_value = MOCKED_YOUTUBE_SOURCE_1
        response = client.put(
            f"{settings.API_V1_PREFIX}/source/{created_source['id']}/fetch",
            headers=superuser_token_headers,
        )
    assert response.status_code == 200
    fetched_source = response.json()
    assert fetched_source["id"] == created_source["id"]

    # Fetch wrong source
    response = client.put(
        f"{settings.API_V1_PREFIX}/source/99999/fetch",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_fetch_all_sources(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """
    Test that a superuser can fetch all sources.
    """
    # Create sources
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_RUMBLE_SOURCE_1["url"]},
    )
    assert response.status_code == 201

    # Fetch All Sources
    with patch("tubecast.crud.source.fetch_all_sources") as mocked_fetch_source:
        mocked_fetch_source.return_value = [MOCKED_YOUTUBE_SOURCE_1, MOCKED_YOUTUBE_SOURCE_1]
        response = client.put(
            f"{settings.API_V1_PREFIX}/source/fetch",
            headers=superuser_token_headers,
        )
        mocked_fetch_source.assert_called_once()

    assert response.status_code == 200
