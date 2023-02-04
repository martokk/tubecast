from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from tests.mock_objects import MOCKED_ITEM_1, MOCKED_ITEMS
from tubecast import crud, models


async def get_mocked_source(db: Session) -> models.Source:
    """
    Create a mocked source.
    """
    # Create an source with an owner
    owner = await crud.user.get(db=db, username="test_user")
    source_create = models.SourceCreate(**MOCKED_ITEM_1)

    return await crud.source.create_with_owner_id(db=db, obj_in=source_create, owner_id=owner.id)


async def test_create_source(db_with_user: Session) -> None:
    """
    Test creating a new source with an owner.
    """
    created_source = await get_mocked_source(db=db_with_user)

    # Check the source was created
    assert created_source.title == MOCKED_ITEM_1["title"]
    assert created_source.description == MOCKED_ITEM_1["description"]
    assert created_source.owner_id is not None


async def test_get_source(db_with_user: Session) -> None:
    """
    Test getting an source by id.
    """
    created_source = await get_mocked_source(db=db_with_user)

    # Get the source
    db_source = await crud.source.get(db=db_with_user, id=created_source.id)
    assert db_source
    assert db_source.id == created_source.id
    assert db_source.title == created_source.title
    assert db_source.description == created_source.description
    assert db_source.owner_id == created_source.owner_id


async def test_update_source(db_with_user: Session) -> None:
    """
    Test updating an source.
    """
    created_source = await get_mocked_source(db=db_with_user)

    # Update the source
    db_source = await crud.source.get(db=db_with_user, id=created_source.id)
    db_source_update = models.SourceUpdate(description="New Description")
    updated_source = await crud.source.update(
        db=db_with_user, id=created_source.id, obj_in=db_source_update
    )
    assert db_source.id == updated_source.id
    assert db_source.title == updated_source.title
    assert updated_source.description == "New Description"
    assert db_source.owner_id == updated_source.owner_id


async def test_update_source_without_filter(db_with_user: Session) -> None:
    """
    Test updating an source without a filter.
    """
    created_source = await get_mocked_source(db=db_with_user)

    # Update the source (without a filter)
    await crud.source.get(db=db_with_user, id=created_source.id)
    db_source_update = models.SourceUpdate(description="New Description")
    with pytest.raises(ValueError):
        await crud.source.update(db=db_with_user, obj_in=db_source_update)


async def test_delete_source(db_with_user: Session) -> None:
    """
    Test deleting an source.
    """
    created_source = await get_mocked_source(db=db_with_user)

    # Delete the source
    await crud.source.remove(db=db_with_user, id=created_source.id)
    with pytest.raises(crud.RecordNotFoundError):
        await crud.source.get(db=db_with_user, id=created_source.id)


async def test_delete_source_delete_error(db_with_user: Session, mocker: MagicMock) -> None:
    """
    Test deleting an source with a delete error.
    """
    mocker.patch("tubecast.crud.source.get", return_value=None)
    with pytest.raises(crud.DeleteError):
        await crud.source.remove(db=db_with_user, id="00000001")


async def test_get_all_sources(db_with_user: Session) -> None:
    """
    Test getting all sources.
    """
    # Create some sources
    for i, source in enumerate(MOCKED_ITEMS):
        source_create = models.SourceCreate(**source)
        await crud.source.create_with_owner_id(
            db=db_with_user, obj_in=source_create, owner_id=f"0000000{i}"
        )

    # Get all sources
    sources = await crud.source.get_all(db=db_with_user)
    assert len(sources) == len(MOCKED_ITEMS)
