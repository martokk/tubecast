from unittest.mock import MagicMock

import pytest
from sqlmodel import Session

from app import crud, models
from app.models.source_video_link import SourceOrderBy
from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1


async def test_create_item(db: Session, source_1: models.Source) -> None:
    """
    Test creating a new item.
    """
    assert source_1.name == MOCKED_RUMBLE_SOURCE_1["name"]
    assert source_1.url == MOCKED_RUMBLE_SOURCE_1["url"]
    assert source_1.description == MOCKED_RUMBLE_SOURCE_1["description"]


async def test_create_item_from_url(db: Session, normal_user: models.User) -> None:
    """
    Test creating a new item from a url.
    """
    url = MOCKED_RUMBLE_SOURCE_1["url"]
    source = await crud.source.create_source_from_url(db=db, url=url, user_id=normal_user.id)
    assert source.name == MOCKED_RUMBLE_SOURCE_1["name"]
    assert source.url == MOCKED_RUMBLE_SOURCE_1["url"]
    assert source.description == MOCKED_RUMBLE_SOURCE_1["description"]


async def test_get_item(db: Session, source_1: models.Source) -> None:
    """
    Test getting an item by id.
    """
    db_source = await crud.source.get(db=db, id=source_1.id)
    assert db_source
    assert db_source.id == source_1.id
    assert db_source.name == source_1.name
    assert db_source.description == source_1.description


async def test_update_item(db: Session, source_1: models.Source) -> None:
    """
    Test updating an item.
    """

    # Update the item
    db_source = await crud.source.get(db=db, id=source_1.id)
    db_source_update = models.SourceUpdate(description="New Description")
    updated_source = await crud.source.update(db=db, id=source_1.id, obj_in=db_source_update)
    assert db_source.id == updated_source.id
    assert db_source.name == updated_source.name
    assert updated_source.description == "New Description"


async def test_update_item_without_filter(db: Session, source_1: models.Source) -> None:
    """
    Test updating an item without a filter.
    """

    # Attempt Update the item without a filter
    await crud.source.get(db=db, id=source_1.id)
    db_source_update = models.SourceUpdate(description="New Description")
    with pytest.raises(ValueError):
        await crud.source.update(db=db, obj_in=db_source_update)


async def test_update_item_reverse_order(db: Session, source_1_w_videos: models.Source) -> None:
    """
    Test updating an item's ordered by
    """

    assert source_1_w_videos.reverse_import_order is False
    assert len(source_1_w_videos.videos) == 2

    source_update = models.SourceUpdate(reverse_import_order=True)

    db_source = await crud.source.update(db=db, id=source_1_w_videos.id, obj_in=source_update)
    assert db_source.reverse_import_order == source_update.reverse_import_order
    assert len(db_source.videos) == 0


async def test_delete_item(db: Session, source_1: models.Source) -> None:
    """
    Test deleting an item.
    """

    # Delete the item
    await crud.source.remove(db=db, id=source_1.id)
    with pytest.raises(crud.RecordNotFoundError):
        await crud.source.get(db=db, id=source_1.id)


async def test_delete_item_without_id(db: Session, source_1: models.Source) -> None:
    """
    Test deleting an item when id is missing.
    """
    # Delete the item (missing id)
    with pytest.raises(ValueError):
        await crud.source.remove(db=db)


async def test_delete_item_delete_error(db: Session, mocker: MagicMock) -> None:
    """
    Test deleting an item with a delete error.
    """
    mocker.patch("app.crud.source.get", return_value=None)
    with pytest.raises(crud.DeleteError):
        await crud.source.remove(db=db, id="00000001")
