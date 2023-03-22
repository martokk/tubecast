from unittest.mock import patch

import pytest
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import DownloadError, YoutubeDLError

from app.services.ytdlp import (
    YDL_OPTS_BASE,
    Http410Error,
    IsDeletedVideoError,
    IsLiveEventError,
    IsPrivateVideoError,
    NoUploadsError,
    PlaylistNotFoundError,
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

    # Test raises exception when info_dict is None.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.return_value = None

        with pytest.raises(YoutubeDLError) as raised:
            info_dict_none = await get_info_dict(
                url=url, ydl_opts=ydl_opts, ie_key=ie_key, custom_extractors=custom_extractors
            )
            assert mocked_extract_info.called
            assert raised.match("yt-dlp did not download a info_dict object.")
            assert info_dict_none is None

    # Test raises exception when YoutubeDL.extract_info raises exception.
    url = "https://nonexistent-video.com"

    with pytest.raises(YoutubeDLError) as raised:
        await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)
        assert raised.match("yt-dlp could not extract info for")

    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = IsLiveEventError("this live event will begin in 1 hour")

        with pytest.raises(IsLiveEventError) as raised:
            await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)
            assert raised.match("this live event will begin in")

    # Test raises exception when info dict is_live.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.return_value = {"is_live": True}

        with pytest.raises(IsLiveEventError) as raised:
            await get_info_dict(
                url=url, ydl_opts=ydl_opts, ie_key=ie_key, custom_extractors=custom_extractors
            )
            assert mocked_extract_info.called
            assert raised.match("yt-dlp did not download a info_dict object.")


async def test_get_info_dict_errors() -> None:
    """
    Test `get_info_dict` errors.
    """
    url = "https://nonexistent-video.com"

    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("This channel has no uploads")
        with pytest.raises(NoUploadsError):
            await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)

    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("The playlist does not exist.")
        with pytest.raises(PlaylistNotFoundError):
            await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)

    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("No video formats found.")
        with pytest.raises(IsLiveEventError):
            await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)

    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("this live event will begin in")
        with pytest.raises(IsLiveEventError):
            await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)

    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("[Private video]")
        with pytest.raises(IsPrivateVideoError):
            await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)

    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = YoutubeDLError("[Deleted video]")
        with pytest.raises(IsDeletedVideoError):
            await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)

    # Test raises exception when live event is starting soon.
    with patch("yt_dlp.YoutubeDL.extract_info") as mocked_extract_info:
        mocked_extract_info.side_effect = DownloadError("HTTP Error 410")
        with pytest.raises(Http410Error):
            await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)
