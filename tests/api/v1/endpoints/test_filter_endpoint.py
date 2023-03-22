from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import paths, settings
from app.models import Filter, Source, SourceOrderBy, User


def test_create_filter(
    db: Session,
    normal_user: User,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    source_1: Source,
    client: TestClient,
) -> None:
    """
    Test that a normal user can create a source from a URL.
    """
    new_filter = {
        "name": "Test Filter 1",
    }

    response = client.post(
        f"{settings.API_V1_PREFIX}/source/{source_1.id}/filter",
        headers=normal_user_token_headers,
        json=new_filter,
    )
    assert response.status_code == status.HTTP_201_CREATED
    result = response.json()
    assert result["source_id"] == result["source_id"]
    assert result["name"] == result["name"]
    assert result["created_by"] == normal_user.id


def test_read_filter(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    filter_1: Filter,
) -> None:
    """
    Test that a superuser can read an source.
    """
    response = client.get(
        f"{settings.API_V1_PREFIX}/filter/{filter_1.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    assert result["source_id"] == filter_1.source.id
    assert result["name"] == filter_1.name

    # Test not found for normal user
    response = client.get(
        f"{settings.API_V1_PREFIX}/filter/invalid_id",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test not found for superuser
    response = client.get(
        f"{settings.API_V1_PREFIX}/filter/invalid_id",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_filter(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    filter_1: Filter,
) -> None:
    """
    Test that a normal user can update a criteria.
    """

    # Update all fields
    updated_filter = {"ordered_by": SourceOrderBy.CREATED_AT.value}
    assert filter_1.ordered_by != updated_filter["ordered_by"]

    response = client.patch(
        f"{settings.API_V1_PREFIX}/filter/{filter_1.id}",
        headers=normal_user_token_headers,
        json=updated_filter,
    )

    assert response.status_code == status.HTTP_200_OK

    result = response.json()
    assert result["id"] == filter_1.id
    assert result["source_id"] == filter_1.source.id
    assert result["name"] == filter_1.name
    assert result["ordered_by"] == updated_filter["ordered_by"]

    # Test not found for normal user
    response = client.patch(
        f"{settings.API_V1_PREFIX}/filter/invalid_id",
        headers=normal_user_token_headers,
        json=updated_filter,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test not found for superuser
    response = client.patch(
        f"{settings.API_V1_PREFIX}/filter/invalid_id",
        headers=superuser_token_headers,
        json=updated_filter,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_filter(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    filter_1: Filter,
) -> None:
    """
    Test that a normal user can delete a criteria.
    """
    response = client.delete(
        f"{settings.API_V1_PREFIX}/filter/{filter_1.id}",
        headers=normal_user_token_headers,
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Make sure the criteria was deleted
    response = client.get(
        f"{settings.API_V1_PREFIX}/filter/{filter_1.id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Test not found for normal user
    response = client.delete(
        f"{settings.API_V1_PREFIX}/filter/invalid_id",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test not found for superuser
    response = client.delete(
        f"{settings.API_V1_PREFIX}/filter/invalid_id",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_filter_rss_feed(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    filter_1: Filter,
) -> None:
    """
    Test that a valid rss file is returned.
    """
    # Delete the rss file
    rss_file_path = paths.FEEDS_PATH / f"{filter_1.id}.rss"
    rss_file_path.unlink(missing_ok=True)

    # Check that the rss file was created
    response = client.put(
        f"{settings.API_V1_PREFIX}/filter/{filter_1.id}/feed",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert "<rss" in str(response.content)
    assert "/rss>" in str(response.content)

    # Test not found for superuser
    response = client.put(
        f"{settings.API_V1_PREFIX}/filter/invalid_id/feed",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
