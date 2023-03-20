from datetime import datetime, timedelta

from sqlmodel import Session

from app import crud, models
from app.models.source_video_link import SourceOrderBy
from app.services.source import (
    delete_orphaned_source_videos,
    fetch_all_sources,
    fetch_source,
    get_source_videos_from_source_info_dict,
)
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
    fetch_results: models.FetchResults = await fetch_all_sources(db=db_with_user)

    # Assert the results
    assert fetch_results.sources == 2
    assert fetch_results.added_videos == 4
    assert fetch_results.refreshed_videos == 4
    assert fetch_results.deleted_videos == 0


async def test_source_videos_sorted(
    db_with_user: Session, source_1_w_videos: models.Source
) -> None:
    """
    Test Source.videos_sorted() if ordered_by is RELEASED_AT.
    """
    ordered_by = SourceOrderBy.RELEASED_AT.value

    # Assert videos are already sorted.
    source_videos = source_1_w_videos.videos.copy()
    assert source_1_w_videos.videos_sorted(ordered_by=ordered_by) == source_videos

    # Change created_at of first video. Move to end of list.
    first_video = source_1_w_videos.videos.pop(0)
    first_video.created_at = first_video.created_at - timedelta(days=1000)
    source_1_w_videos.videos.append(first_video)
    assert source_1_w_videos.videos != source_videos
    assert first_video == source_1_w_videos.videos[-1]

    # Sort videos by released_at
    sorted_videos = source_1_w_videos.videos_sorted(ordered_by=SourceOrderBy.RELEASED_AT.value)
    assert sorted_videos == source_videos
    assert first_video == sorted_videos[0]

    # Sort videos by created_at
    sorted_videos = source_1_w_videos.videos_sorted(ordered_by=SourceOrderBy.CREATED_AT.value)
    assert first_video == sorted_videos[1]
