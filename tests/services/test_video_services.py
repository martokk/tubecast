from unittest.mock import ANY, patch

from sqlmodel import Session
from yt_dlp.utils import YoutubeDLError

from app import crud, models
from app.services.video import fetch_videos, refresh_all_videos
from app.services.ytdlp import IsLiveEventError
from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1, MOCKED_RUMBLE_SOURCE_2


async def test_refresh_all_videos(db_with_user: Session) -> None:
    """
    Tests 'refresh_all_videos', fetching new data from yt-dlp for all Videos.
    """
    # Create source
    user = await crud.user.get(db=db_with_user, username="test_user")
    await crud.source.create_source_from_url(
        db=db_with_user, url=MOCKED_RUMBLE_SOURCE_1["url"], user_id=user.id
    )
    await crud.source.create_source_from_url(
        db=db_with_user, url=MOCKED_RUMBLE_SOURCE_2["url"], user_id=user.id
    )

    # Refresh all videos older than 0 hours
    with patch("app.services.video.refresh_videos") as mocked_refresh_videos:
        await refresh_all_videos(db=db_with_user, older_than_hours=0)
        assert mocked_refresh_videos.call_count == 1
        mocked_refresh_videos.assert_called_with(videos_needing_refresh=ANY, db=ANY)

    # Refresh all videos older than 0 hours
    with patch("app.services.video.refresh_videos") as mocked_refresh_videos:
        await refresh_all_videos(db=db_with_user, older_than_hours=999)
        assert mocked_refresh_videos.call_count == 1
        mocked_refresh_videos.assert_called_with(videos_needing_refresh=ANY, db=ANY)


async def test_fetch_videos(db_with_user: Session) -> None:
    """
    Tests 'fetch_videos', fetching new data for a list of videos from yt-dlp.
    """
    # Create source
    user = await crud.user.get(db=db_with_user, username="test_user")
    source = await crud.source.create_source_from_url(
        db=db_with_user, url=MOCKED_RUMBLE_SOURCE_1["url"], user_id=user.id
    )

    videos = [models.Video(**video) for video in MOCKED_RUMBLE_SOURCE_1["videos"]]
    source.videos = videos

    with patch("app.services.video.fetch_video", return_value=videos[0]):
        fetched_videos = await fetch_videos(videos=videos, db=db_with_user)
        assert len(fetched_videos) == len(videos)

    # Test that videos that are live events are ignored
    with patch("app.services.video.fetch_video", side_effect=IsLiveEventError):
        fetched_videos = await fetch_videos(videos=videos, db=db_with_user)
        assert len(fetched_videos) == 0

    # Test that videos with errors are ignored
    with patch("app.services.video.fetch_video", side_effect=YoutubeDLError):
        fetched_videos = await fetch_videos(videos=videos, db=db_with_user)
        assert len(fetched_videos) == 0
