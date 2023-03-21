from unittest.mock import ANY, patch

from sqlmodel import Session
from yt_dlp.utils import YoutubeDLError

from app import crud, models
from app.services.video import fetch_videos, refresh_all_videos
from app.services.ytdlp import IsLiveEventError
from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1, MOCKED_RUMBLE_SOURCE_2


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
