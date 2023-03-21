import pytest
from sqlmodel import Session

from app import crud, models
from app.services.source import fetch_source


async def test_create_video_from_url_already_exists(
    db: Session, normal_user: models.User, source_1: models.Source
) -> None:
    """
    Test that the create_video_from_url function returns a response with the correct status code.
    """
    await fetch_source(db=db, id=source_1.id)

    with pytest.raises(crud.RecordAlreadyExistsError):
        await crud.video.create_video_from_url(db=db, url=source_1.videos[0].url)
