import datetime

import pytest

from app.handlers.rumble import RumbleHandler
from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1, get_mocked_source_info_dict


async def test_map_video_info_dict_entity_to_video_dict() -> None:
    """
    Tests the `map_video_info_dict_entity_to_video_dict` function.
    """
    handler = RumbleHandler()
    mocked_source_info_dict = await get_mocked_source_info_dict(url=MOCKED_RUMBLE_SOURCE_1["url"])
    mocked_entry_info_dict = mocked_source_info_dict["entries"][0]

    video_dict = handler.map_video_info_dict_entity_to_video_dict(
        entry_info_dict=mocked_entry_info_dict
    )
    assert video_dict["title"] == mocked_entry_info_dict["title"]
    assert video_dict["uploader"] == mocked_entry_info_dict["uploader"]
    assert video_dict["uploader_id"] == mocked_entry_info_dict["channel"]
    assert video_dict["description"] == mocked_entry_info_dict["description"]
    assert video_dict["duration"] == mocked_entry_info_dict["duration"]
    assert video_dict["url"] == mocked_entry_info_dict["original_url"]
    assert video_dict["media_url"] == mocked_entry_info_dict["formats"][0]["url"]
    assert video_dict["media_filesize"] == mocked_entry_info_dict["formats"][0]["filesize"]
    assert video_dict["thumbnail"] == mocked_entry_info_dict["thumbnail"]
    assert video_dict["released_at"] == datetime.datetime.utcfromtimestamp(
        mocked_entry_info_dict["timestamp"]
    )

    # Test is_live
    mocked_entry_info_dict = mocked_source_info_dict["entries"][0]
    mocked_entry_info_dict["live_status"] = "is_live"
    assert mocked_entry_info_dict["formats"][0]["filesize"] != 0
    assert mocked_entry_info_dict["formats"][0]["url"] is not None

    video_dict = handler.map_video_info_dict_entity_to_video_dict(
        entry_info_dict=mocked_entry_info_dict
    )

    assert video_dict["media_url"] is None
    assert video_dict["media_filesize"] == 0

    # Test is_upcoming
    mocked_entry_info_dict = mocked_source_info_dict["entries"][0]
    mocked_entry_info_dict["live_status"] = "is_upcoming"
    assert mocked_entry_info_dict["formats"][0]["filesize"] != 0
    assert mocked_entry_info_dict["formats"][0]["url"] is not None

    video_dict = handler.map_video_info_dict_entity_to_video_dict(
        entry_info_dict=mocked_entry_info_dict
    )

    assert video_dict["media_url"] is None
    assert video_dict["media_filesize"] == 0

    # Test if format_id not in format_info_dict
    mocked_entry_info_dict["format_id"] = "not_in_format_info_dict"
    with pytest.raises(ValueError):
        video_dict = handler.map_video_info_dict_entity_to_video_dict(
            entry_info_dict=mocked_entry_info_dict
        )
