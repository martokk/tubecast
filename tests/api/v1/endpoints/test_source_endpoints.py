from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import settings
from tests.mock_objects import MOCKED_SOURCES, MOCKED_YOUTUBE_SOURCE_1


def test_create_source_from_url(
    client: TestClient,
    db: Session,
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
    assert source["handler"] == MOCKED_YOUTUBE_SOURCE_1["handler"]
    assert source["author"] == MOCKED_YOUTUBE_SOURCE_1["author"]
    assert source["description"] == MOCKED_YOUTUBE_SOURCE_1["description"]
    assert source["extractor"] == MOCKED_YOUTUBE_SOURCE_1["extractor"]
    assert source["created_at"] is not None
    assert source["updated_at"] is not None


def test_create_duplicate_source(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test a duplicate source cannot be created.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=MOCKED_YOUTUBE_SOURCE_1,
    )
    assert response.status_code == 201

    # Try to create a duplicate source
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=MOCKED_YOUTUBE_SOURCE_1,
    )
    assert response.status_code == 409
    duplicate = response.json()
    assert duplicate["detail"] == "Source already exists"


def test_read_source(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """
    Test that a superuser can read an source.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=MOCKED_YOUTUBE_SOURCE_1,
    )
    assert response.status_code == 201
    created_source = response.json()

    # Read Source
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/{created_source['id']}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    read_source = response.json()

    assert read_source["url"] == MOCKED_YOUTUBE_SOURCE_1["url"]
    assert read_source["name"] == MOCKED_YOUTUBE_SOURCE_1["name"]
    assert read_source["logo"] == MOCKED_YOUTUBE_SOURCE_1["logo"]
    assert read_source["ordered_by"] == MOCKED_YOUTUBE_SOURCE_1["ordered_by"]
    assert read_source["handler"] == MOCKED_YOUTUBE_SOURCE_1["handler"]
    assert read_source["author"] == MOCKED_YOUTUBE_SOURCE_1["author"]
    assert read_source["description"] == MOCKED_YOUTUBE_SOURCE_1["description"]
    assert read_source["extractor"] == MOCKED_YOUTUBE_SOURCE_1["extractor"]
    assert read_source["created_by"] is not None
    assert read_source["created_at"] is not None
    assert read_source["updated_at"] is not None


def test_get_source_not_found(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """
    Test that a source not found error is returned.
    """
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/1",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Source not found"


def test_get_source_forbidden(
    db: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that a forbidden error is returned.
    """
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/5kwf8hFn",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_superuser_get_all_sources(
    db: Session,  # pylint: disable=unused-argument
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    """
    Test that a superuser can get all sources.
    """

    # Create 3 sources
    for source in MOCKED_SOURCES:
        response = client.post(
            f"{settings.API_V1_PREFIX}/source/",
            headers=superuser_token_headers,
            json=source,
        )
        assert response.status_code == 201

    # Get all sources as superuser
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) == 3


def test_normal_user_get_all_sources(
    db: Session,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    """
    Test that a normal user can get all their own sources.
    """
    # Create 2 sources as normal user
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
        json=MOCKED_SOURCES[0],
    )
    assert response.status_code == 201
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
        json=MOCKED_SOURCES[1],
    )
    assert response.status_code == 201

    # Create 1 source as super user
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=MOCKED_SOURCES[2],
    )
    assert response.status_code == 201

    # Get all sources as normal user
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) == 2


def test_update_source(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """
    Test that a superuser can update an source.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=MOCKED_YOUTUBE_SOURCE_1,
    )
    assert response.status_code == 201
    created_source = response.json()

    # Update Source
    update_data = MOCKED_YOUTUBE_SOURCE_1.copy()
    update_data["name"] = "Updated Name"
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
    db: Session, client: TestClient, normal_user_token_headers: dict[str, str]
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


def test_delete_source(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
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
    db: Session,
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


def test_delete_source_forbidden(
    db: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that a forbidden error is returned.
    """
    response = client.delete(
        f"{settings.API_V1_PREFIX}/source/5kwf8hFn",
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
    with patch("app.services.fetch.fetch_source") as mocked_fetch_source:
        response = client.put(
            f"{settings.API_V1_PREFIX}/source/{created_source['id']}/fetch",
            headers=superuser_token_headers,
        )
    assert response.status_code == 202

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
        json={"url": MOCKED_SOURCES[0]["url"]},
    )
    assert response.status_code == 201
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_SOURCES[1]["url"]},
    )
    assert response.status_code == 201

    # Fetch All Sources
    with patch("app.api.v1.endpoints.source.fetch_all_sources") as mock_fetch_all_sources:
        response = client.put(
            f"{settings.API_V1_PREFIX}/source/fetch",
            headers=superuser_token_headers,
        )
        assert response.status_code == 202
        assert mock_fetch_all_sources.call_count == 1
        assert response.json() == {"msg": "Fetching all sources in the background."}


def test_get_source_rss_feed(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    """
    Test that a valid rss file is returned.
    """
    # Check that the rss file doesn't exist
    response = client.get(
        f"/source/{MOCKED_YOUTUBE_SOURCE_1['id']}/feed",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404

    # Create a source
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    created_source = response.json()

    # Check that the rss file was created
    response = client.get(
        f"/source/{created_source['id']}/feed",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert "<rss" in str(response.content)
    assert "/rss>" in str(response.content)

    # Delete the rss file
    response = client.delete(
        f"/api/v1/source/{created_source['id']}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 204

    # Check that the rss file was deleted
    response = client.get(
        f"/source/{created_source['id']}/feed",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
