from sqlmodel import Session

from app import crud
from app.services.source import (
    delete_orphaned_source_videos,
    fetch_source,
    get_source_videos_from_source_info_dict,
)
from tests.mock_objects import (
    MOCKED_RUMBLE_SOURCE_1,
    MOCKED_RUMBLE_VIDEO_3,
    get_mocked_source_info_dict,
)


async def test_get_source_videos_from_source_info_dict() -> None:
    """
    Test `get_source_videos_from_source_info_dict` when playlist is not nested.
    """
    mocked_source_info_dict = await get_mocked_source_info_dict(url=MOCKED_RUMBLE_SOURCE_1["url"])
    mocked_source_info_dict["source_id"] = MOCKED_RUMBLE_SOURCE_1["id"]

    videos = get_source_videos_from_source_info_dict(source_info_dict=mocked_source_info_dict)

    assert len(videos) == 2
    result_video = videos[0]
    mocked_video = MOCKED_RUMBLE_SOURCE_1["videos"][0]

    assert result_video.title == mocked_video["title"]
    assert result_video.description == mocked_video["description"]
    assert result_video.duration == mocked_video["duration"]
    assert result_video.thumbnail == mocked_video["thumbnail"]
    assert result_video.url == mocked_video["url"]


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


async def test_delete_orphaned_source_videos(db_with_user: Session) -> None:
    """
    Tests 'delete_orphaned_source_videos', deleting videos that are no longer in the source.
    """
    # Create fetched_source
    user = await crud.user.get(db=db_with_user, username="test_user")
    created_source = await crud.source.create_source_from_url(
        db=db_with_user, url=MOCKED_RUMBLE_SOURCE_1["url"], user_id=user.id
    )
    await fetch_source(db=db_with_user, id=created_source.id)

    fetched_source = await crud.source.get(db=db_with_user, id=created_source.id)
    assert len(fetched_source.videos) == 2
    fetched_videos = list(fetched_source.videos)

    # Add video to db_source
    video = await crud.video.create_video_from_url(
        db=db_with_user, url=MOCKED_RUMBLE_VIDEO_3["url"]
    )
    fetched_source.videos.append(video)

    # Get db_source Videos
    source = await crud.source.get(db=db_with_user, id=fetched_source.id)
    assert len(source.videos) == 3

    # Delete orphaned videos
    deleted_videos = await delete_orphaned_source_videos(
        db=db_with_user, fetched_videos=fetched_videos, db_source=source
    )

    # Check that videos were deleted
    assert len(deleted_videos) == 1
    assert deleted_videos[0].title == MOCKED_RUMBLE_VIDEO_3["title"]

    # Check that videos were deleted from database
    source = await crud.source.get(db=db_with_user, id=fetched_source.id)
    assert len(source.videos) == 2
