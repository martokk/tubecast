from fastapi.testclient import TestClient
from sqlmodel import Session

from tubecast import settings

TEST_ITEM = {
    "uploader": "test",
    "uploader_id": "test_uploader_id",
    "title": "Example source 1",
    "description": "This is example source 1.",
    "duration": 417,
    "thumbnail": "https://sp.rmbl.ws/s8d/R/0_FRh.oq1b.jpg",
    "url": "https://rumble.com/1111111/test.html",
}


def test_create_item(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """
    Test that a superuser can create a new item.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=TEST_ITEM,
    )
    assert response.status_code == 201
    item = response.json()
    assert item["uploader"] == TEST_ITEM["uploader"]
    assert item["uploader_id"] == TEST_ITEM["uploader_id"]
    assert item["title"] == TEST_ITEM["title"]
    assert item["description"] == TEST_ITEM["description"]
    assert item["duration"] == TEST_ITEM["duration"]
    assert item["thumbnail"] == TEST_ITEM["thumbnail"]
    assert item["url"] == TEST_ITEM["url"]
    assert "id" in item
    assert "owner_id" in item


def test_create_duplicate_item(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """
    Test a duplicate item cannot be created.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=TEST_ITEM,
    )
    assert response.status_code == 201

    # Try to create a duplicate item
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=TEST_ITEM,
    )
    assert response.status_code == 200
    duplicate = response.json()
    assert duplicate["detail"] == "source already exists"


def test_read_item(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """
    Test that a superuser can read an item.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=TEST_ITEM,
    )
    assert response.status_code == 201
    created_item = response.json()

    # Read Item
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/{created_item['id']}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    read_item = response.json()

    assert read_item["uploader"] == TEST_ITEM["uploader"]
    assert read_item["uploader_id"] == TEST_ITEM["uploader_id"]
    assert read_item["title"] == TEST_ITEM["title"]
    assert read_item["description"] == TEST_ITEM["description"]
    assert read_item["duration"] == TEST_ITEM["duration"]
    assert read_item["thumbnail"] == TEST_ITEM["thumbnail"]
    assert read_item["url"] == TEST_ITEM["url"]


def test_get_item_not_found(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """
    Test that a item not found error is returned.
    """
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/1",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "source not found"


def test_get_item_forbidden(
    db_with_sources: Session, client: TestClient, normal_user_token_headers: dict[str, str]
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


def test_superuser_get_all_items(
    db_with_sources: Session, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test that a superuser can get all items.
    """
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 3


def test_normal_user_get_all_items(
    db_with_sources: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that a normal user can get all thier own items.
    """
    response = client.get(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 3


def test_update_item(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """
    Test that a superuser can update an item.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=TEST_ITEM,
    )
    assert response.status_code == 201
    created_item = response.json()

    # Update Item
    update_data = TEST_ITEM.copy()
    update_data["title"] = "Updated Title"
    response = client.patch(
        f"{settings.API_V1_PREFIX}/source/{created_item['id']}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response.status_code == 200
    updated_item = response.json()
    assert updated_item["title"] == update_data["title"]

    # Update wrong item
    response = client.patch(
        f"{settings.API_V1_PREFIX}/source/99999",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response.status_code == 404


def test_update_item_forbidden(
    db_with_sources: Session, client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """
    Test that a forbidden error is returned.
    """
    response = client.patch(
        f"{settings.API_V1_PREFIX}/source/5kwf8hFn",
        headers=normal_user_token_headers,
        json=TEST_ITEM,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_delete_item(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """
    Test that a superuser can delete an item.
    """
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=superuser_token_headers,
        json=TEST_ITEM,
    )
    assert response.status_code == 201
    created_item = response.json()

    # Delete Item
    response = client.delete(
        f"{settings.API_V1_PREFIX}/source/{created_item['id']}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 204

    # Delete wrong item
    response = client.delete(
        f"{settings.API_V1_PREFIX}/source/99999",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_delete_item_forbidden(
    db_with_sources: Session, client: TestClient, normal_user_token_headers: dict[str, str]
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
