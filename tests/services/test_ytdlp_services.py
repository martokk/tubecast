from unittest.mock import patch

import pytest
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import DownloadError, YoutubeDLError

from app.services.ytdlp import (
    YDL_OPTS_BASE,
    AccountNotFoundError,
    FormatNotFoundError,
    Http410Error,
    IsDeletedVideoError,
    IsLiveEventError,
    IsPrivateVideoError,
    NoUploadsError,
    PlaylistNotFoundError,
    VideoUnavailableError,
    get_info_dict,
)
from tests.mock_objects import MOCKED_RUMBLE_VIDEO_3, get_mocked_video_info_dict


async def test_get_info_dict() -> None:
    """
    Test `get_info_dict`.
    """
    ydl_opts = {"test": True}
    url = MOCKED_RUMBLE_VIDEO_3["url"]
    ie_key = "ie_key"
    custom_extractors = [InfoExtractor]

    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.return_value = await get_mocked_video_info_dict(url=url)
        info_dict = await get_info_dict(
            url=url, ydl_opts=ydl_opts, ie_key=ie_key, custom_extractors=custom_extractors
        )

    assert mocked_extract_info.called

    assert info_dict["title"] == MOCKED_RUMBLE_VIDEO_3["title"]
    assert info_dict["description"] == MOCKED_RUMBLE_VIDEO_3["description"]
    assert info_dict["duration"] == MOCKED_RUMBLE_VIDEO_3["duration"]
    assert info_dict["thumbnail"] == MOCKED_RUMBLE_VIDEO_3["thumbnail"]
    assert info_dict["metadata"]["url"] == MOCKED_RUMBLE_VIDEO_3["url"]
    assert info_dict["metadata"]["ydl_opts"] == ydl_opts
    assert info_dict["metadata"]["ie_key"] == ie_key
    assert info_dict["metadata"]["custom_extractors"] == custom_extractors


async def test_get_info_dict_none() -> None:
    # Test raises exception when info_dict is None.

    ydl_opts = {"test": True}
    url = MOCKED_RUMBLE_VIDEO_3["url"]
    ie_key = "ie_key"
    custom_extractors = [InfoExtractor]

    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.return_value = None

        with pytest.raises(YoutubeDLError) as raised:
            info_dict_none = await get_info_dict(
                url=url, ydl_opts=ydl_opts, ie_key=ie_key, custom_extractors=custom_extractors
            )
            assert mocked_extract_info.called
            assert raised.match("yt-dlp did not download a info_dict object.")
            assert info_dict_none is None


async def test_get_info_dict_could_not_extract() -> None:
    # Test raises exception when YoutubeDL.extract_info raises exception.
    url = "https://nonexistent-video.com"

    with pytest.raises(YoutubeDLError) as raised:
        await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)
        assert raised.match("yt-dlp could not extract info for")


async def test_get_info_dict_live_event_starts_soon() -> None:
    # Test raises exception when live event is starting soon.
    url = "https://live.com"
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = IsLiveEventError("this live event will begin in 1 hour")

        with pytest.raises(IsLiveEventError) as raised:
            await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)
            assert raised.match("this live event will begin in")


async def test_get_info_dict_live_event() -> None:
    # Test raises exception when info dict is_live.
    ydl_opts = {"test": True}
    url = MOCKED_RUMBLE_VIDEO_3["url"]
    ie_key = "ie_key"
    custom_extractors = [InfoExtractor]

    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.return_value = {"is_live": True}

        with pytest.raises(IsLiveEventError) as raised:
            await get_info_dict(
                url=url, ydl_opts=ydl_opts, ie_key=ie_key, custom_extractors=custom_extractors
            )
            assert mocked_extract_info.called
            assert raised.match("yt-dlp did not download a info_dict object.")


async def test_get_info_dict_account_terminated() -> None:
    # Test raises exception when info dict is_live.
    url = "http://youtube.com/user/thisaccounthasbeenterminated"
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("This account has been terminated.")
        with pytest.raises(AccountNotFoundError):
            await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)


async def test_get_info_dict_unavailable_video() -> None:
    url = "http://youtube.com/watch?v=unavailablevideo"
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("Video unavailable")
        with pytest.raises(VideoUnavailableError):
            await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)


async def test_get_info_dict_channel_no_uploads() -> None:
    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("This channel has no uploads")
        with pytest.raises(NoUploadsError):
            await get_info_dict("https://test.com", ydl_opts=YDL_OPTS_BASE)


async def test_get_info_dict_playlist_does_not_exist() -> None:
    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("The playlist does not exist.")
        with pytest.raises(PlaylistNotFoundError):
            await get_info_dict("https://test.com", ydl_opts=YDL_OPTS_BASE)


async def test_get_info_dict_no_format_found() -> None:
    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("No video formats found.")
        with pytest.raises(IsLiveEventError):
            await get_info_dict("https://test.com", ydl_opts=YDL_OPTS_BASE)


async def test_get_info_dict_live_starting_soon() -> None:
    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("this live event will begin in")
        with pytest.raises(IsLiveEventError):
            await get_info_dict("https://test.com", ydl_opts=YDL_OPTS_BASE)


async def test_get_info_dict_private_video() -> None:
    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("[Private video]")
        with pytest.raises(IsPrivateVideoError):
            await get_info_dict("https://test.com", ydl_opts=YDL_OPTS_BASE)


async def test_get_info_dict_deleted_video() -> None:
    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("[Deleted video]")
        with pytest.raises(IsDeletedVideoError):
            await get_info_dict("https://test.com", ydl_opts=YDL_OPTS_BASE)


async def test_get_info_dict_410_gone() -> None:
    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = DownloadError("HTTP Error 410")
        with pytest.raises(Http410Error):
            await get_info_dict("https://test.com", ydl_opts=YDL_OPTS_BASE)


async def test_get_info_dict_requested_format_not_found() -> None:
    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("Requested format is not available.")
        with pytest.raises(FormatNotFoundError):
            await get_info_dict("https://test.com", ydl_opts=YDL_OPTS_BASE)
