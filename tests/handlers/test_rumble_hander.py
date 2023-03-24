from typing import Any

from unittest.mock import ANY

import pytest

from app.handlers.exceptions import AwaitingTranscodingError, FormatNotFoundError, InvalidSourceUrl
from app.handlers.rumble import RumbleHandler as Handler
from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1, get_mocked_source_info_dict


@pytest.fixture(name="handler")
async def fixture_handler() -> Handler:
    return Handler()


@pytest.fixture(name="mocked_source")
async def fixture_mocked_source() -> dict[str, Any]:
    return MOCKED_RUMBLE_SOURCE_1


@pytest.fixture(name="mocked_source_info_dict")
async def fixture_mocked_source_info_dict(mocked_source: dict[str, Any]) -> dict[str, Any]:
    return await get_mocked_source_info_dict(url=mocked_source["url"])


@pytest.fixture(name="mocked_entry_info_dict")
async def fixture_mocked_entry_info_dict(mocked_source_info_dict: dict[str, Any]) -> dict[str, Any]:
    mocked_entry_info_dict: dict[str, Any] = mocked_source_info_dict["entries"][0]
    return mocked_entry_info_dict


def test_sanitize_source_url(handler: Handler) -> None:
    url1 = "https://www.rumble.com/c/AnnVandersteel"
    assert handler.sanitize_source_url(url1) == url1.lower()

    url2 = "https://rumble.com/c/AnnVandersteel"
    assert handler.sanitize_source_url(url2) == url1.lower()

    url3 = "https://www.rumble.com/user/Doug-texeira"
    assert handler.sanitize_source_url(url3) == url3.lower()

    with pytest.raises(InvalidSourceUrl):
        handler.sanitize_source_url(url="https://www.rumble.com/xxxxxxxxxxxxxxxx")

    with pytest.raises(InvalidSourceUrl):
        handler.get_channel_url_from_c_url(url="https://www.rumble.com/xxxxxxxxxxxxxxxx")

    with pytest.raises(InvalidSourceUrl):
        handler.get_channel_url_from_user_url(url="https://www.rumble.com/xxxxxxxxxxxxxxxx")


def test_get_video_ydl_opts(handler: Handler) -> None:
    """
    Test get_video_ydl_opts function.
    """
    assert handler.get_video_ydl_opts() == {
        "format": "worst[ext=mp4]",
        "skip_download": True,
        "simulate": True,
        "ignore_no_formats_error": True,
        "allowed_extractors": ["CustomRumbleIE", "CustomRumbleEmbed", "CustomRumbleChannel"],
    }


async def test_get_source_info_dict_kwargs(handler: Handler) -> None:
    """
    Test get_source_info_dict_kwargs function.
    """
    # Test url with '/c/' in it
    url = "https://www.rumble.com/c/AnimalsDoingThings"
    result = await handler.get_source_info_dict_kwargs(url)
    assert result == {
        "extract_flat": True,
        "playlistreverse": True,
        "playlistend": 50,
        "dateafter": "now-20y",
    }

    # Test url with '/user/' in it
    url = "https://www.rumble.com/user/AwesomeVideos"
    result = await handler.get_source_info_dict_kwargs(url)
    assert result == {
        "extract_flat": True,
        "playlistreverse": True,
        "playlistend": 50,
        "dateafter": "now-20y",
    }

    # Test url with neither '/c/' nor '/user/' in it
    url = "https://www.rumble.com/v123456"
    try:
        await handler.get_source_info_dict_kwargs(url)
    except InvalidSourceUrl as e:
        assert str(e) == f"Source info dict kwargs not found for url: ({str(url)})"


async def test_map_source_info_dict_to_source_dict_with_thumbnail(
    handler: Handler, mocked_source: dict[str, Any], mocked_source_info_dict: dict[str, Any]
) -> None:
    data = {
        "url": mocked_source["url"],
        "name": mocked_source["name"],
        "author": mocked_source["author"],
        "logo": mocked_source["logo"],
        "ordered_by": "released_at",
        "description": mocked_source["description"],
        "videos": mocked_source["videos"],
        "extractor": mocked_source["extractor"],
    }
    assert (
        handler.map_source_info_dict_to_source_dict(
            mocked_source_info_dict, mocked_source["videos"]
        )
        == data
    )


async def test_map_source_info_dict_to_source_dict_without_thumbnail(
    handler: Handler, mocked_source: dict[str, Any], mocked_source_info_dict: dict[str, Any]
) -> None:
    mocked_source_info_dict = mocked_source_info_dict.copy()
    mocked_source_info_dict.pop("thumbnail")
    mocked_source_info_dict["url"] = mocked_source["url"]
    logo = f"/static/logos/{mocked_source['id']}.png"
    data = {
        "url": mocked_source["url"],
        "name": mocked_source["name"],
        "author": mocked_source["author"],
        "logo": logo,
        "ordered_by": "released_at",
        "description": mocked_source["description"],
        "videos": mocked_source["videos"],
        "extractor": mocked_source["extractor"],
    }
    assert (
        handler.map_source_info_dict_to_source_dict(
            mocked_source_info_dict, mocked_source["videos"]
        )
        == data
    )


async def test_map_source_info_dict_entity_to_video_dict(
    handler: Handler, mocked_source: dict[str, Any], mocked_entry_info_dict: dict[str, Any]
) -> None:
    video = mocked_source["videos"][0]
    data = {
        "source_id": mocked_source["id"],
        "url": video["url"],
        "added_at": ANY,
        "title": video["title"],
        "description": video["description"],
        "duration": video["duration"],
        "thumbnail": video["thumbnail"],
        "released_at": ANY,
        "media_url": None,
        "media_filesize": None,
    }
    assert (
        handler.map_source_info_dict_entity_to_video_dict(
            source_id=mocked_source["id"], entry_info_dict=mocked_entry_info_dict
        )
        == data
    )


async def test_map_video_info_dict_entity_to_video_dict_live_status(
    handler: Handler, mocked_source: dict[str, Any], mocked_entry_info_dict: dict[str, Any]
) -> None:
    video = mocked_source["videos"][0]
    entry_info_dict = mocked_entry_info_dict.copy()
    entry_info_dict["live_status"] = "is_live"
    data = {
        "title": video["title"],
        "uploader": video["uploader"],
        "uploader_id": video["uploader_id"],
        "description": video["description"],
        "duration": video["duration"],
        "url": video["url"],
        "media_url": None,
        "media_filesize": 0,
        "thumbnail": video["thumbnail"],
        "released_at": ANY,
    }
    result = handler.map_video_info_dict_entity_to_video_dict(entry_info_dict=entry_info_dict)
    assert result == data

    # Test if format_id not in format_info_dict
    mocked_entry_info_dict["format_id"] = "not_in_format_info_dict"
    with pytest.raises(ValueError):
        handler.map_video_info_dict_entity_to_video_dict(entry_info_dict=mocked_entry_info_dict)


async def test_map_video_info_dict_entity_to_video_dict_format_id_keyerror(
    handler: Handler, mocked_entry_info_dict: dict[str, Any]
) -> None:
    with pytest.raises(FormatNotFoundError):
        entry_info_dict = mocked_entry_info_dict.copy()
        entry_info_dict.pop("format_id")
        handler.map_video_info_dict_entity_to_video_dict(entry_info_dict=entry_info_dict)

    with pytest.raises(FormatNotFoundError):
        entry_info_dict = mocked_entry_info_dict.copy()
        entry_info_dict.pop("formats")
        handler.map_video_info_dict_entity_to_video_dict(entry_info_dict=entry_info_dict)

    with pytest.raises(AwaitingTranscodingError):
        entry_info_dict = mocked_entry_info_dict.copy()
        entry_info_dict.pop("formats")
        entry_info_dict["awaiting_transcoding"] = True
        handler.map_video_info_dict_entity_to_video_dict(entry_info_dict=entry_info_dict)
