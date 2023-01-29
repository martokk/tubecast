from unittest.mock import MagicMock

import pytest
from sqlmodel import Session

from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1, MOCKED_YOUTUBE_SOURCE_1
from tubecast import crud, models


async def create_source(db: Session) -> models.Source:
    """
    Create a source in the database.
    """
    source = await crud.source.create(db=db, in_obj=models.SourceCreate(**MOCKED_YOUTUBE_SOURCE_1))
    assert source.name == MOCKED_YOUTUBE_SOURCE_1["name"]
    assert source.url == MOCKED_YOUTUBE_SOURCE_1["url"]
    assert source.description == MOCKED_YOUTUBE_SOURCE_1["description"]
    return source


async def test_create_item(db_with_user: Session) -> None:
    """
    Test creating a new item.
    """
    source = await create_source(db=db_with_user)
    assert source.name == MOCKED_YOUTUBE_SOURCE_1["name"]
    assert source.url == MOCKED_YOUTUBE_SOURCE_1["url"]
    assert source.description == MOCKED_YOUTUBE_SOURCE_1["description"]


async def test_create_item_from_url(db_with_user: Session) -> None:
    """
    Test creating a new item from a url.
    """
    owner = await crud.user.get(db=db_with_user, username="test_user")
    url = MOCKED_YOUTUBE_SOURCE_1["url"]
    source = await crud.source.create_source_from_url(db=db_with_user, url=url, user_id=owner.id)
    assert source.name == MOCKED_YOUTUBE_SOURCE_1["name"]
    assert source.url == MOCKED_YOUTUBE_SOURCE_1["url"]
    assert source.description == MOCKED_YOUTUBE_SOURCE_1["description"]


async def test_get_item(db: Session) -> None:
    """
    Test getting an item by id.
    """
    # Create a new item
    source = await create_source(db=db)

    # Get the item by id
    db_source = await crud.source.get(db=db, id=source.id)
    assert db_source
    assert db_source.id == source.id
    assert db_source.name == source.name
    assert db_source.description == source.description


async def test_update_item(db: Session) -> None:
    """
    Test updating an item.
    """
    # Create a new item
    source = await create_source(db=db)

    # Update the item
    db_source = await crud.source.get(db=db, id=source.id)
    db_source_update = models.SourceUpdate(description="New Description")
    updated_source = await crud.source.update(db=db, id=source.id, in_obj=db_source_update)
    assert db_source.id == updated_source.id
    assert db_source.name == updated_source.name
    assert updated_source.description == "New Description"


async def test_update_item_without_filter(db: Session) -> None:
    """
    Test updating an item without a filter.
    """
    # Create a new item
    source = await create_source(db=db)

    # Attempt Update the item without a filter
    await crud.source.get(db=db, id=source.id)
    db_source_update = models.SourceUpdate(description="New Description")
    with pytest.raises(ValueError):
        await crud.source.update(db=db, in_obj=db_source_update)


async def test_delete_item(db: Session) -> None:
    """
    Test deleting an item.
    """
    # Create a new item
    source = await create_source(db=db)

    # Delete the item
    await crud.source.remove(db=db, id=source.id)
    with pytest.raises(crud.RecordNotFoundError):
        await crud.source.get(db=db, id=source.id)


async def test_delete_item_delete_error(db: Session, mocker: MagicMock) -> None:
    """
    Test deleting an item with a delete error.
    """
    mocker.patch("tubecast.crud.source.get", return_value=None)
    with pytest.raises(crud.DeleteError):
        await crud.source.remove(db=db, id="00000001")


async def test_fetch_all_sources(db_with_user: Session) -> None:
    """
    Test fetching all sources.
    """
    # Create 2 sources
    user = await crud.user.get(db=db_with_user, username="test_user")
    await crud.source.create_source_from_url(
        db=db_with_user, url=MOCKED_RUMBLE_SOURCE_1["url"], user_id=user.id
    )
    await crud.source.create_source_from_url(
        db=db_with_user, url=MOCKED_YOUTUBE_SOURCE_1["url"], user_id=user.id
    )

    # Fetch all sources
    fetch_results: models.FetchResults = await crud.source.fetch_all_sources(db=db_with_user)

    # Assert the results
    assert fetch_results.sources == 2
    assert fetch_results.added_videos == 4
    assert fetch_results.refreshed_videos == 4
    assert fetch_results.deleted_videos == 0
