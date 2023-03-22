from unittest.mock import ANY, Mock, patch

from sqlmodel import Session
from yt_dlp.utils import YoutubeDLError

from app import crud, models
from app.handlers.exceptions import FormatNotFoundError
from app.services.video import fetch_videos, get_videos_needing_refresh, refresh_all_videos
from app.services.ytdlp import IsLiveEventError, IsPrivateVideoError
from tests.mock_objects import MOCKED_RUMBLE_SOURCE_2


async def test_refresh_all_videos(
    db: Session, normal_user: models.User, source_1: models.Source
) -> None:
    """
    Tests 'refresh_all_videos', fetching new data from yt-dlp for all Videos.
    """
    # Create another source
    await crud.source.create_source_from_url(
        db=db, url=MOCKED_RUMBLE_SOURCE_2["url"], user_id=normal_user.id
    )

    # Refresh all videos older than 0 hours
    with patch("app.services.video.refresh_videos") as mocked_refresh_videos:
        await refresh_all_videos(db=db)
        assert mocked_refresh_videos.call_count == 1
        mocked_refresh_videos.assert_called_with(videos_needing_refresh=ANY, db=ANY)

    # Refresh all videos older than 0 hours
    with patch("app.services.video.refresh_videos") as mocked_refresh_videos:
        await refresh_all_videos(db=db)
        assert mocked_refresh_videos.call_count == 1
        mocked_refresh_videos.assert_called_with(videos_needing_refresh=ANY, db=ANY)


async def test_fetch_videos(
    db: Session, normal_user: models.User, source_1_w_videos: models.Source
) -> None:
    """
    Tests 'fetch_videos', fetching new data for a list of videos from yt-dlp.
    """
    with patch("app.services.video.fetch_video", return_value=source_1_w_videos.videos[0]):
        fetched_videos = await fetch_videos(videos=source_1_w_videos.videos, db=db)
        assert len(fetched_videos) == len(source_1_w_videos.videos)

    # Test that videos that are live events are ignored
    with patch("app.services.video.fetch_video", side_effect=IsLiveEventError):
        fetched_videos = await fetch_videos(videos=source_1_w_videos.videos, db=db)
        assert len(fetched_videos) == 0

    # Test that videos with errors are ignored
    with patch("app.services.video.fetch_video", side_effect=YoutubeDLError):
        fetched_videos = await fetch_videos(videos=source_1_w_videos.videos, db=db)
        assert len(fetched_videos) == 0

    # Test that videos that are not found are ignored
    with patch("app.services.video.fetch_video", side_effect=crud.RecordNotFoundError):
        fetched_videos = await fetch_videos(videos=source_1_w_videos.videos, db=db)
        assert len(fetched_videos) == 0

    # Test that videos that are not found are ignored
    with patch("app.services.video.fetch_video", side_effect=FormatNotFoundError):
        fetched_videos = await fetch_videos(videos=source_1_w_videos.videos, db=db)
        assert len(fetched_videos) == 0

    # Test that videos that are not found are ignored
    assert len(source_1_w_videos.videos) == 2
    with patch("app.services.video.fetch_video", side_effect=IsPrivateVideoError):
        fetched_videos = await fetch_videos(videos=source_1_w_videos.videos, db=db)
        assert len(fetched_videos) == 0
        assert len(source_1_w_videos.videos) == 0


def test_get_videos_needing_refresh(
    mocker: Mock, db: Session, normal_user: models.User, source_1_w_videos: models.Source
) -> None:
    """
    Tests 'get_videos_needing_refresh', getting videos that need to be refreshed.
    """
    # Get videos that need to be refreshed
    videos_needing_refresh = get_videos_needing_refresh(videos=source_1_w_videos.videos)
    assert len(videos_needing_refresh) == 0

    # Get videos that need to be refreshed
    videos = source_1_w_videos.videos
    videos[0].media_url = None
    videos_needing_refresh = get_videos_needing_refresh(videos=source_1_w_videos.videos)
    assert len(videos_needing_refresh) == 1

    # Get videos that need to be refreshed
    videos = source_1_w_videos.videos
    videos[0].media_url = None
    videos[0].title = "[Deleted video]"
    videos[1].media_url = None
    videos_needing_refresh = get_videos_needing_refresh(videos=source_1_w_videos.videos)
    assert len(videos_needing_refresh) == 1
