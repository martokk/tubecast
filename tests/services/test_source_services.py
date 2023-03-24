from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session

from app import crud, models, paths
from app.models import Source
from app.models.source import SourceUpdate
from app.models.source_video_link import SourceOrderBy
from app.services.source import (
    FetchCancelledError,
    delete_orphaned_source_videos,
    fetch_all_sources,
    fetch_source,
    get_source_videos_from_source_info_dict,
)
from app.services.ytdlp import AccountNotFoundError
from tests.mock_objects import (
    MOCKED_RUMBLE_SOURCE_1,
    MOCKED_RUMBLE_VIDEO_3,
    MOCKED_YOUTUBE_SOURCE_1,
    get_mocked_source_info_dict,
)


async def test_get_source_videos_from_source_info_dict() -> None:
    """
    Test `get_source_videos_from_source_info_dict` when playlist is not nested.
    """

    # Get mocked source info dict
    mocked_source_info_dict = await get_mocked_source_info_dict(url=MOCKED_RUMBLE_SOURCE_1["url"])
    mocked_source_info_dict["source_id"] = MOCKED_RUMBLE_SOURCE_1["id"]

    # Get videos from source info dict
    videos = get_source_videos_from_source_info_dict(source_info_dict=mocked_source_info_dict)

    # Assert the results
    assert len(videos) == 2
    result_video = videos[0]
    mocked_video = MOCKED_RUMBLE_SOURCE_1["videos"][0]

    assert result_video.title == mocked_video["title"]
    assert result_video.description == mocked_video["description"]
    assert result_video.duration == mocked_video["duration"]
    assert result_video.thumbnail == mocked_video["thumbnail"]
    assert result_video.url == mocked_video["url"]

    # Handle Deleted Video
    mocked_source_info_dict["entries"][0]["title"] = "[Deleted Video]"
    videos = get_source_videos_from_source_info_dict(source_info_dict=mocked_source_info_dict)
    assert len(videos) == 1

    # Handle Private Video
    mocked_source_info_dict["entries"][0]["title"] = "[Private Video]"
    videos = get_source_videos_from_source_info_dict(source_info_dict=mocked_source_info_dict)
    assert len(videos) == 1


async def test_get_nested_source_videos_from_source_info_dict() -> None:
    """
    Test `get_source_videos_from_source_info_dict` when playlist is nested.
    """
    mocked_source_info_dict = await get_mocked_source_info_dict(url=MOCKED_RUMBLE_SOURCE_1["url"])
    mocked_source_info_dict["source_id"] = MOCKED_RUMBLE_SOURCE_1["id"]
    mocked_source_info_dict["entries"] = [
        {"entries": mocked_source_info_dict["entries"], "_type": "playlist"}
    ]

    videos = get_source_videos_from_source_info_dict(source_info_dict=mocked_source_info_dict)

    assert len(videos) == 2
    result_video = videos[0]
    mocked_video = MOCKED_RUMBLE_SOURCE_1["videos"][0]

    assert result_video.title == mocked_video["title"]
    assert result_video.description == mocked_video["description"]
    assert result_video.duration == mocked_video["duration"]
    assert result_video.thumbnail == mocked_video["thumbnail"]
    assert result_video.url == mocked_video["url"]


async def test_delete_orphaned_source_videos(
    db: Session, normal_user: models.User, source_1: models.Source
) -> None:
    """
    Tests 'delete_orphaned_source_videos', deleting videos that are no longer in the source.
    """
    await fetch_source(db=db, id=source_1.id)

    fetched_source = await crud.source.get(db=db, id=source_1.id)
    assert len(fetched_source.videos) == 2
    fetched_videos = list(fetched_source.videos)

    # Add video to db_source
    video = await crud.video.create_video_from_url(db=db, url=MOCKED_RUMBLE_VIDEO_3["url"])
    fetched_source.videos.append(video)

    # Get db_source Videos
    source = await crud.source.get(db=db, id=fetched_source.id)
    assert len(source.videos) == 3

    # Delete orphaned videos
    deleted_videos = await delete_orphaned_source_videos(
        db=db, fetched_videos=fetched_videos, db_source=source
    )

    # Check that videos were deleted
    assert len(deleted_videos) == 1
    assert deleted_videos[0].title == MOCKED_RUMBLE_VIDEO_3["title"]

    # Check that videos were deleted from database
    source = await crud.source.get(db=db, id=fetched_source.id)
    assert len(source.videos) == 2


async def test_fetch_all_sources(
    db: Session, normal_user: models.User, source_1: models.Source
) -> None:
    """
    Test fetching all sources.
    """
    # Create another source
    new_source = await crud.source.create_source_from_url(
        db=db, url=MOCKED_YOUTUBE_SOURCE_1["url"], user_id=normal_user.id
    )

    # Fetch all sources
    fetch_results: models.FetchResults = await fetch_all_sources(db=db)

    # Assert the results
    assert fetch_results.sources == 2
    assert fetch_results.added_videos == 4
    assert fetch_results.refreshed_videos == 4
    assert fetch_results.deleted_videos == 0

    # Test source.is_deleted
    await crud.source.update(db=db, id=new_source.id, obj_in=SourceUpdate(is_deleted=True))
    fetch_results = await fetch_all_sources(db=db)

    # Assert the results
    await crud.source.update(
        db=db, id=new_source.id, obj_in=SourceUpdate(is_deleted=False, is_active=False)
    )
    fetch_results = await fetch_all_sources(db=db)
    assert fetch_results.sources == 1


async def test_fetch_all_sources_fetch_canceled_error(
    db: Session, normal_user: models.User, source_1: models.Source
) -> None:
    """
    Test fetching all sources.
    """
    # Create another source
    await crud.source.create_source_from_url(
        db=db, url=MOCKED_YOUTUBE_SOURCE_1["url"], user_id=normal_user.id
    )

    # Fetch all sources
    fetch_results: models.FetchResults = await fetch_all_sources(db=db)

    # Assert the results
    assert fetch_results.sources == 2
    assert fetch_results.added_videos == 4
    assert fetch_results.refreshed_videos == 4
    assert fetch_results.deleted_videos == 0

    with patch("app.services.source.fetch_source") as mocked_fetch_source:
        mocked_fetch_source.side_effect = FetchCancelledError()
        fetch_results = await fetch_all_sources(db=db)

    assert fetch_results.sources == 0


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_fetch_source_create_logo(mocker: Mock, db: Session, source_1: models.Source) -> None:
    """
    Fetch source and create logo.
    """

    logo_path = paths.LOGOS_PATH / f"{source_1.id}.png"
    logo_path.unlink(missing_ok=True)
    assert logo_path.exists() is False

    db_source = await crud.source.get(db=db, id=source_1.id)
    db_source.logo = f"/static/logos/{source_1.id}.png"
    mocker.patch("app.crud.source.update", return_value=db_source)

    await fetch_source(db=db, id=db_source.id)

    # Create logo
    assert logo_path.exists() is True


async def test_fetch_source_account_not_found_error(db: Session, source_1: Source) -> None:
    """
    Test fetch_source when AccountNotFoundError is raised.
    """
    with patch("app.services.source.get_source_info_dict") as mocked_get_source_info_dict:
        mocked_get_source_info_dict.side_effect = AccountNotFoundError

        with pytest.raises(FetchCancelledError):
            await fetch_source(db=db, id=source_1.id)
