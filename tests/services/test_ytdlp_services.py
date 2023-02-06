from unittest.mock import patch

import pytest
from yt_dlp.extractor.common import InfoExtractor

from tests.mock_objects import MOCKED_RUMBLE_VIDEO_3, get_mocked_video_info_dict
from tubecast.services.ytdlp import YDL_OPTS_BASE, get_info_dict


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

        with pytest.raises(ValueError):
            info_dict_none = await get_info_dict(
                url=url, ydl_opts=ydl_opts, ie_key=ie_key, custom_extractors=custom_extractors
            )
            assert mocked_extract_info.called
            assert info_dict_none is None

    # Test raises exception when YoutubeDL.extract_info raises exception.
    url = "https://nonexistent-video.com"

    with pytest.raises(ValueError, match="yt-dlp could not extract info for"):
        await get_info_dict(url, ydl_opts=YDL_OPTS_BASE)
