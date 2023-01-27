import pytest

from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1, get_mocked_source_info_dict
from tubecast.handlers.rumble import RumbleHandler


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

    # Test if format_id not in format_info_dict
    mocked_entry_info_dict["format_id"] = "not_in_format_info_dict"
    with pytest.raises(ValueError):
        video_dict = handler.map_video_info_dict_entity_to_video_dict(
            entry_info_dict=mocked_entry_info_dict
        )
