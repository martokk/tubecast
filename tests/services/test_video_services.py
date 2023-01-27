from typing import Any

from unittest.mock import ANY, patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1, MOCKED_RUMBLE_SOURCE_2
from tubecast import crud
from tubecast.services.video import refresh_all_videos, refresh_videos

# async def test_refresh_videos(db_with_user: Session, mocker: MagicMock) -> None:
#     """
#     Tests 'refresh_videos', fetching new data from yt-dlp for a list of Videos.
#     """
#     # Create source
#     user = await crud.user.get(db=db_with_user, username="test_user")
#     source = await crud.source.create_source_from_url(
#         db=db_with_user, url=MOCKED_RUMBLE_SOURCE_1["url"], user_id=user.id
#     )

#     # Refresh source
#     refreshed_sources = await refresh_videos(sources=[source], db=db_with_user)

#     assert len(refreshed_sources) == 1


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
    with patch("tubecast.services.video.refresh_videos") as mocked_refresh_videos:
        await refresh_all_videos(db=db_with_user, older_than_hours=0)
        assert mocked_refresh_videos.call_count == 1
        mocked_refresh_videos.assert_called_with(videos=ANY, db=ANY, older_than_hours=0)

    # Refresh all videos older than 0 hours
    with patch("tubecast.services.video.refresh_videos") as mocked_refresh_videos:
        await refresh_all_videos(db=db_with_user, older_than_hours=99999999999999999999)
        assert mocked_refresh_videos.call_count == 1
        mocked_refresh_videos.assert_called_with(
            videos=ANY, db=ANY, older_than_hours=99999999999999999999
        )
