import pytest
from sqlmodel import Session

from app import crud
from app.services.source import fetch_source
from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1


async def test_create_video_from_url_already_exists(
    db_with_user: Session,
) -> None:
    """
    Test that the create_video_from_url function returns a response with the correct status code.
    """
    user = await crud.user.get(db=db_with_user, username="test_user")
    source = await crud.source.create_source_from_url(
        db=db_with_user, url=MOCKED_RUMBLE_SOURCE_1["url"], user_id=user.id
    )
    await fetch_source(db=db_with_user, id=source.id)

    with pytest.raises(crud.RecordAlreadyExistsError):
        await crud.video.create_video_from_url(db=db_with_user, url=source.videos[0].url)
