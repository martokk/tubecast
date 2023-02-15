import pytest

from app.handlers.youtube import YoutubeHandler
from tests.mock_objects import MOCKED_YOUTUBE_SOURCE_1, get_mocked_source_info_dict

HANDLER = YoutubeHandler()


def test_force_watch_v_format() -> None:
    """
    Test that the force_watch_v_format method returns the correct URL.
    """
    # Test regular watch URL
    watch_url = "https://www.youtube.com/watch?v=VIDEO_ID"
    assert HANDLER.force_watch_v_format(url=watch_url) == watch_url

    # Test short URL
    url2 = "https://www.youtube.com/shorts/VIDEO_ID"
    assert HANDLER.force_watch_v_format(url=url2) == watch_url

    # Test invalid URL
    url3 = "https://www.youtube.com/invalid/VIDEO_ID"
    with pytest.raises(ValueError):
        HANDLER.force_watch_v_format(url=url3)


async def test_map_video_info_dict_entity_to_video_dict() -> None:
    """
    Tests the `map_video_info_dict_entity_to_video_dict` function.
    """
    handler = YoutubeHandler()
    mocked_source_info_dict = await get_mocked_source_info_dict(url=MOCKED_YOUTUBE_SOURCE_1["url"])
    mocked_entry_info_dict = mocked_source_info_dict["entries"][0]

    video_dict = handler.map_video_info_dict_entity_to_video_dict(
        entry_info_dict=mocked_entry_info_dict
    )
    assert video_dict["title"] == mocked_entry_info_dict["title"]
    assert video_dict["uploader"] == mocked_entry_info_dict["uploader"]
    assert video_dict["uploader_id"] == mocked_entry_info_dict["channel_id"]
    assert video_dict["description"] == mocked_entry_info_dict["description"]

    # Test if format_id not in format_info_dict
    mocked_entry_info_dict["format_id"] = "not_in_format_info_dict"
    with pytest.raises(ValueError):
        video_dict = handler.map_video_info_dict_entity_to_video_dict(
            entry_info_dict=mocked_entry_info_dict
        )
