from fastapi.testclient import TestClient
from sqlmodel import Session

from tubecast import settings
from tests.mock_objects import MOCKED_ITEM_1, MOCKED_ITEMS


def test_create_source(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """
    Test that a superuser can create a new source.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=MOCKED_VIDEO_1,
    )
    assert response.status_code == 201
    source = response.json()
    assert source["title"] == MOCKED_ITEM_1["title"]
    assert source["description"] == MOCKED_ITEM_1["description"]
    assert source["url"] == MOCKED_ITEM_1["url"]
    assert source["owner_id"] is not None
    assert source["id"] is not None


def test_create_duplicate_source(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test a duplicate source cannot be created.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=MOCKED_VIDEO_1,
    )
    assert response.status_code == 201

    # Try to create a duplicate source
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=MOCKED_VIDEO_1,
    )
    assert response.status_code == 200
    duplicate = response.json()
    assert duplicate["detail"] == "Source already exists"


def test_read_source(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """
    Test that a superuser can read an source.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=MOCKED_VIDEO_1,
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

    assert read_source["title"] == MOCKED_ITEM_1["title"]
    assert read_source["description"] == MOCKED_ITEM_1["description"]
    assert read_source["url"] == MOCKED_ITEM_1["url"]
    assert read_source["owner_id"] is not None
    assert read_source["id"] is not None


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
    db_with_user: Session, client: TestClient, normal_user_token_headers: dict[str, str]
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
    db_with_user: Session,  # pylint: disable=unused-argument
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    """
    Test that a superuser can get all sources.
    """

    # Create 3 sources
    for source in MOCKED_ITEMS:
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
    db_with_user: Session,  # pylint: disable=unused-argument
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
        json=MOCKED_VIDEOS[0],
    )
    assert response.status_code == 201
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
        json=MOCKED_VIDEOS[1],
    )
    assert response.status_code == 201

    # Create 1 source as super user
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=MOCKED_VIDEOS[2],
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
        json=MOCKED_VIDEO_1,
    )
    assert response.status_code == 201
    created_source = response.json()

    # Update Source
    update_data = MOCKED_ITEM_1.copy()
    update_data["title"] = "Updated Title"
    response = client.patch(
        f"{settings.API_V1_PREFIX}/source/{created_source['id']}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response.status_code == 200
    updated_source = response.json()
    assert updated_source["title"] == update_data["title"]

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
        json=MOCKED_VIDEO_1,
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
        json=MOCKED_VIDEO_1,
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


def test_delete_source_forbidden(
    db_with_user: Session, client: TestClient, normal_user_token_headers: dict[str, str]
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
