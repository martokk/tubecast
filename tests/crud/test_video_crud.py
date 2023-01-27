import pytest
from sqlmodel import Session

from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1
from tubecast import crud


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

    with pytest.raises(crud.RecordAlreadyExistsError):
        await crud.video.create_video_from_url(
            db=db_with_user, url=source.videos[0].url, source_id=source.id
        )
