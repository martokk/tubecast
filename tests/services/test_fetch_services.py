from datetime import datetime, timedelta
from unittest.mock import ANY, Mock, patch

import pytest
from sqlmodel import Session
from yt_dlp.utils import YoutubeDLError

from app import crud, paths
from app.models import FetchResults, Source, SourceUpdate, User, Video, VideoUpdate
from app.services.fetch import (
    FetchCanceledError,
    FetchVideoError,
    fetch_all_sources,
    fetch_source,
    fetch_video,
    fetch_videos,
    get_videos_needing_refresh,
    refresh_all_videos,
)
from app.services.ytdlp import (
    AccountNotFoundError,
    FormatNotFoundError,
    IsLiveEventError,
    IsPrivateVideoError,
    VideoUnavailableError,
)
from tests.mock_objects import MOCKED_RUMBLE_SOURCE_2, MOCKED_YOUTUBE_SOURCE_1


# Fetch All Sources
async def test_fetch_all_sources(db: Session, normal_user: User, source_1: Source) -> None:
    """
    Test fetching all sources.
    """
    # Create another source
    new_source = await crud.source.create_source_from_url(
        db=db, url=MOCKED_YOUTUBE_SOURCE_1["url"], user_id=normal_user.id
    )

    # Fetch all sources
    fetch_results: FetchResults = await fetch_all_sources(db=db)

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
    db: Session, normal_user: User, source_1: Source
) -> None:
    """
    Test fetching all sources.
    """
    # Create another source
    await crud.source.create_source_from_url(
        db=db, url=MOCKED_YOUTUBE_SOURCE_1["url"], user_id=normal_user.id
    )

    # Fetch all sources
    fetch_results: FetchResults = await fetch_all_sources(db=db)

    # Assert the results
    assert fetch_results.sources == 2
    assert fetch_results.added_videos == 4
    assert fetch_results.refreshed_videos == 4
    assert fetch_results.deleted_videos == 0

    with patch("app.services.fetch.fetch_source") as mocked_fetch_source:
        mocked_fetch_source.side_effect = FetchCanceledError()
        fetch_results = await fetch_all_sources(db=db)

    assert fetch_results.sources == 0


# Fetch Source
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_fetch_source_create_logo(mocker: Mock, db: Session, source_1: Source) -> None:
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
    with patch("app.services.fetch.get_source_info_dict") as mocked_get_source_info_dict:
        mocked_get_source_info_dict.side_effect = AccountNotFoundError

        with pytest.raises(FetchCanceledError):
            await fetch_source(db=db, id=source_1.id)


# Fetch Videos
async def test_fetch_videos(db: Session, source_1_w_videos: Source) -> None:
    """
    Tests 'fetch_videos', fetching new data for a list of videos from yt-dlp.
    """
    with patch("app.services.fetch.fetch_video", return_value=source_1_w_videos.videos[0]):
        fetched_videos = await fetch_videos(videos=source_1_w_videos.videos, db=db)
        assert len(fetched_videos) == len(source_1_w_videos.videos)


async def test_fetch_videos_unavailable(
    db: Session, normal_user: User, source_1_w_videos: Source
) -> None:
    # Test that videos that are not found are ignored
    assert len(source_1_w_videos.videos) == 2
    with patch("app.services.fetch.get_video_info_dict", side_effect=VideoUnavailableError):
        fetched_videos = await fetch_videos(videos=source_1_w_videos.videos, db=db)
        assert len(fetched_videos) == 0
        assert len(source_1_w_videos.videos) == 0


# Fetch Video
async def test_fetch_video_unavailable_error(db: Session, source_1_w_videos: Source) -> None:
    # Test that videos recent videos are ignored via FetchCanceledError
    video1: Video = source_1_w_videos.videos[0]
    video1 = await crud.video.update(
        db=db, id=video1.id, obj_in=VideoUpdate(released_at=datetime.utcnow() - timedelta(hours=1))
    )
    with patch("app.services.fetch.get_video_info_dict", side_effect=IsPrivateVideoError):
        with pytest.raises(FetchCanceledError):
            await fetch_video(db=db, video_id=video1.id)

    # Test Errors from videos released more than 36 hour ago are not ignored
    video2 = source_1_w_videos.videos[0]
    video2 = await crud.video.update(
        db=db, id=video2.id, obj_in=VideoUpdate(released_at=datetime.utcnow() - timedelta(hours=37))
    )
    with patch("app.services.fetch.get_video_info_dict", side_effect=IsPrivateVideoError):
        with pytest.raises(FetchCanceledError):
            await fetch_video(db=db, video_id=video2.id)


async def test_fetch_video_Exception(db: Session, source_1_w_videos: Source) -> None:
    """
    Test fetch_video when Exception is raised.
    """
    # Test that videos recent videos are ignored via FetchCanceledError
    video1: Video = source_1_w_videos.videos[0]
    video1 = await crud.video.update(
        db=db, id=video1.id, obj_in=VideoUpdate(released_at=datetime.utcnow() - timedelta(hours=1))
    )
    with patch("app.services.fetch.get_video_info_dict", side_effect=IsPrivateVideoError):
        with pytest.raises(FetchCanceledError):
            await fetch_video(db=db, video_id=video1.id)

    # Test Errors from videos released more than 36 hour ago are not ignored
    video2 = source_1_w_videos.videos[0]
    video2 = await crud.video.update(
        db=db, id=video2.id, obj_in=VideoUpdate(released_at=datetime.utcnow() - timedelta(hours=37))
    )
    with patch("app.services.fetch.get_video_info_dict", side_effect=IsPrivateVideoError):
        with pytest.raises(FetchCanceledError):
            await fetch_video(db=db, video_id=video2.id)


async def test_fetch_video_record_not_found(db: Session, source_1_w_videos: Source) -> None:
    """
    Test fetch_video when RecordNotFoundError is raised.
    """
    video1: Video = source_1_w_videos.videos[0]
    with patch("app.services.fetch.get_video_info_dict", side_effect=crud.RecordNotFoundError):
        with pytest.raises(crud.RecordNotFoundError):
            await fetch_video(db=db, video_id=video1.id)


async def test_fetch_video_youtubedl_error(db: Session, source_1_w_videos: Source) -> None:
    """
    Test fetch_video when RecordNotFoundError is raised.
    """
    video1: Video = source_1_w_videos.videos[0]
    with patch("app.services.fetch.get_video_info_dict", side_effect=YoutubeDLError):
        with pytest.raises(FetchCanceledError):
            await fetch_video(db=db, video_id=video1.id)


# Refresh All Videos
async def test_refresh_all_videos(db: Session, normal_user: User, source_1: Source) -> None:
    """
    Tests 'refresh_all_videos', fetching new data from yt-dlp for all Videos.
    """
    # Create another source
    await crud.source.create_source_from_url(
        db=db, url=MOCKED_RUMBLE_SOURCE_2["url"], user_id=normal_user.id
    )

    # Refresh all videos older than 0 hours
    with patch("app.services.fetch.refresh_videos") as mocked_refresh_videos:
        await refresh_all_videos(db=db)
        assert mocked_refresh_videos.call_count == 1
        mocked_refresh_videos.assert_called_with(videos=ANY, db=ANY)


# Refresh Videos
def test_get_videos_needing_refresh(
    mocker: Mock, db: Session, normal_user: User, source_1_w_videos: Source
) -> None:
    """
    Tests 'get_videos_needing_refresh', getting videos that need to be refreshed.
    """
    # Ensure no videos need to be refreshed
    videos_needing_refresh = get_videos_needing_refresh(videos=source_1_w_videos.videos)
    assert len(videos_needing_refresh) == 0

    # Test 1 video needs to be refreshed
    videos = source_1_w_videos.videos
    videos[0].media_url = None
    videos_needing_refresh = get_videos_needing_refresh(videos=source_1_w_videos.videos)
    assert len(videos_needing_refresh) == 1

    # Test deleted videos don't need to be refreshed
    videos = source_1_w_videos.videos
    videos[0].media_url = None
    videos[0].title = "[Deleted video]"
    videos[1].media_url = None
    videos_needing_refresh = get_videos_needing_refresh(videos=source_1_w_videos.videos)
    assert len(videos_needing_refresh) == 1
