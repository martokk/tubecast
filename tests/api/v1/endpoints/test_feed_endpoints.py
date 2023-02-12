from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.mock_objects import MOCKED_YOUTUBE_SOURCE_1
from tubecast import settings


def test_build_rss(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    """
    Test that a valid rss file is returned.
    """
    # Check that the rss file doesn't exist
    response = client.get(
        "/feed/iQEQPfeQ",
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

    # Build the rss
    response = client.put(
        f"/api/v1/feed/{created_source['id']}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert "<rss" in str(response.content)
    assert "/rss>" in str(response.content)

    # Check that the rss file was created
    response = client.get(
        f"/feed/{created_source['id']}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200

    # Delete the rss file
    response = client.delete(
        f"/api/v1/feed/{created_source['id']}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 204

    # Check that the rss file was deleted
    response = client.get(
        f"/feed/{created_source['id']}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_build_rss_invalid_source(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    """
    Test that a 404 is returned when the source doesn't exist.
    """
    # Check that the rss file doesn't exist
    response = client.get(
        "/feed/iQEQPfeQ",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404

    # Build the rss
    response = client.put(
        "/api/v1/feed/iQEQPfeQ",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_delete_rss_invalid_source(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    """
    Test that a 404 is returned when the source doesn't exist.
    """
    # Check that the rss file doesn't exist
    response = client.get(
        "/feed/iQEQPfeQ",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404

    # Delete the rss file
    response = client.delete(
        "/api/v1/feed/iQEQPfeQ",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
