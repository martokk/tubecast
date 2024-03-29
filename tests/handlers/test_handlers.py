from typing import Any

import pytest

from app.handlers import get_handler_from_string, get_handler_from_url
from app.handlers.base import ServiceHandler
from app.handlers.exceptions import HandlerNotFoundError
from app.services.ytdlp import AwaitingTranscodingError, FormatNotFoundError


def test_get_handler_from_url() -> None:
    """
    Tests the `get_handler_from_url` function.
    """
    url = "https://www.youtube.com/watch?v=1234567890"
    handler = get_handler_from_url(url=url)
    assert handler.__class__.__name__ == "YoutubeHandler"

    url = "https://www.rumble.com/v1234567890"
    handler = get_handler_from_url(url=url)
    assert handler.__class__.__name__ == "RumbleHandler"

    url = "https://www.bitchute.com/video/1234567890"
    with pytest.raises(HandlerNotFoundError):
        get_handler_from_url(url=url)


def test_get_handler_from_string() -> None:
    """
    Tests the `get_handler_from_string` function.
    """
    handler_string = "YoutubeHandler"
    handler = get_handler_from_string(handler_string=handler_string)
    assert handler.__class__.__name__ == "YoutubeHandler"

    handler_string = "RumbleHandler"
    handler = get_handler_from_string(handler_string=handler_string)
    assert handler.__class__.__name__ == "RumbleHandler"

    handler_string = "BitchuteHandler"
    with pytest.raises(HandlerNotFoundError):
        get_handler_from_string(handler_string=handler_string)


async def test_map_video_info_dict_entity_to_video_dict_format_id_keyerror(
    mocked_entry_info_dict: dict[str, Any]
) -> None:
    # Test missing format_id key
    with pytest.raises(FormatNotFoundError):
        entry_info_dict = mocked_entry_info_dict.copy()
        entry_info_dict.pop("format_id")
        ServiceHandler()._get_format_info_dict_from_entry_info_dict(entry_info_dict=entry_info_dict)  # type: ignore

    # Test missing formats key
    with pytest.raises(FormatNotFoundError):
        entry_info_dict = mocked_entry_info_dict.copy()
        entry_info_dict.pop("formats")
        ServiceHandler()._get_format_info_dict_from_entry_info_dict(entry_info_dict=entry_info_dict)  # type: ignore

    # Test missing formats key, but awaiting_transcoding is True
    with pytest.raises(AwaitingTranscodingError):
        entry_info_dict = mocked_entry_info_dict.copy()
        entry_info_dict.pop("formats")
        entry_info_dict["awaiting_transcoding"] = True
        ServiceHandler()._get_format_info_dict_from_entry_info_dict(entry_info_dict=entry_info_dict)  # type: ignore

    # Test m3u8 in url
    with pytest.raises(AwaitingTranscodingError):
        entry_info_dict = mocked_entry_info_dict.copy()
        entry_info_dict["formats"][0]["url"] = "https://somedomain.com/somepath.m3u8"
        ServiceHandler()._get_format_info_dict_from_entry_info_dict(entry_info_dict=entry_info_dict)  # type: ignore
