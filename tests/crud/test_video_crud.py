from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from tubecast import crud, models


async def test_create_item(db_with_user: Session) -> None:
    """
    Test creating a new item with an owner.
    """
    owner = await crud.user.get(db=db_with_user, username="test_user")
    source_create = models.SourceCreate(
        id="12345678",
        uploader="test",
        uploader_id="test_uploader_id",
        title="Example source AAA",
        description="This is example source AAA.",
        duration=417,
        thumbnail="https://sp.rmbl.ws/s8d/R/0_FRh.oq1b.jpg",
        url="https://rumble.com/AAA/test.html",
    )
    source = await crud.source.create_with_owner_id(
        db=db_with_user, in_obj=source_create, owner_id=owner.id
    )
    assert source.title == "Example source AAA"
    assert source.description == "This is example source AAA."
    assert source.owner_id == owner.id


async def test_get_item(db_with_sources: Session) -> None:
    """
    Test getting an item by id.
    """
    db_source = await crud.source.get(db=db_with_sources, id="00000000")
    assert db_source
    assert db_source.id == "00000000"
    assert db_source.title == "Example source 0"
    assert db_source.description == "This is example source 0."
    assert db_source.owner_id == "ZbFPeSXW"


async def test_update_item(db_with_sources: Session) -> None:
    """
    Test updating an item.
    """
    db_source = await crud.source.get(db=db_with_sources, id="00000000")
    db_source_update = models.SourceUpdate(description="New Description")
    updated_source = await crud.source.update(
        db=db_with_sources, id="00000000", in_obj=db_source_update
    )
    assert db_source.id == updated_source.id
    assert db_source.title == updated_source.title
    assert updated_source.description == "New Description"
    assert db_source.owner_id == updated_source.owner_id


async def test_update_item_without_filter(db_with_sources: Session) -> None:
    """
    Test updating an item without a filter.
    """
    await crud.source.get(db=db_with_sources, id="00000000")
    db_source_update = models.SourceUpdate(description="New Description")
    with pytest.raises(ValueError):
        await crud.source.update(db=db_with_sources, in_obj=db_source_update)


async def test_delete_item(db_with_sources: Session) -> None:
    """
    Test deleting an item.
    """
    await crud.source.remove(db=db_with_sources, id="00000000")
    with pytest.raises(crud.RecordNotFoundError):
        await crud.source.get(db=db_with_sources, id="00000000")


async def test_delete_item_delete_error(db_with_sources: Session, mocker: MagicMock) -> None:
    """
    Test deleting an item with a delete error.
    """
    mocker.patch("tubecast.crud.source.get", return_value=None)
    with pytest.raises(crud.DeleteError):
        await crud.source.remove(db=db_with_sources, id="00000001")
