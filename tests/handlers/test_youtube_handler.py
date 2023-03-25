from typing import Any

from unittest.mock import ANY

import pytest

from app.handlers.exceptions import FormatNotFoundError, InvalidSourceUrl
from app.handlers.youtube import YoutubeHandler as Handler
from app.models.source_video_link import SourceOrderBy
from app.services.ytdlp import Http410Error, IsDeletedVideoError, IsPrivateVideoError
from tests.mock_objects import MOCKED_YOUTUBE_SOURCE_1, get_mocked_source_info_dict


@pytest.fixture(name="handler")
async def fixture_handler() -> Handler:
    return Handler()


@pytest.fixture(name="mocked_source")
async def fixture_mocked_source() -> dict[str, Any]:
    return MOCKED_YOUTUBE_SOURCE_1


@pytest.fixture(name="mocked_source_info_dict")
async def fixture_mocked_source_info_dict(mocked_source: dict[str, Any]) -> dict[str, Any]:
    return await get_mocked_source_info_dict(url=mocked_source["url"])


@pytest.fixture(name="mocked_entry_info_dict")
async def fixture_mocked_entry_info_dict(mocked_source_info_dict: dict[str, Any]) -> dict[str, Any]:
    mocked_entry_info_dict: dict[str, Any] = mocked_source_info_dict["entries"][0]
    return mocked_entry_info_dict


def test_force_watch_v_format(handler: Handler) -> None:
    """
    Test that the force_watch_v_format method returns the correct URL.
    """
    # Test regular watch URL
    watch_url = "https://www.youtube.com/watch?v=VIDEO_ID"
    assert handler.force_watch_v_format(url=watch_url) == watch_url

    # Test short URL
    url2 = "https://www.youtube.com/shorts/VIDEO_ID"
    assert handler.force_watch_v_format(url=url2) == watch_url

    # Test invalid URL
    url3 = "https://www.youtube.com/invalid/VIDEO_ID"
    with pytest.raises(ValueError):
        handler.force_watch_v_format(url=url3)


async def test_map_video_info_dict_entity_to_video_dict(
    handler: Handler, mocked_source: dict[str, Any]
) -> None:
    """
    Tests the `map_video_info_dict_entity_to_video_dict` function.
    """
    mocked_source_info_dict = await get_mocked_source_info_dict(url=mocked_source["url"])
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


def test_sanitize_source_url(handler: Handler) -> None:
    url1 = "https://youtube.com/@Styxhexenhammer666"
    assert (
        handler.sanitize_source_url(url1)
        == "https://www.youtube.com/channel/UC0rZoXAD5lxgBHMsjrGwWWQ"
    )

    url1 = "https://www.youtube.com/@Styxhexenhammer666"
    assert (
        handler.sanitize_source_url(url1)
        == "https://www.youtube.com/channel/UC0rZoXAD5lxgBHMsjrGwWWQ"
    )

    url2 = "https://www.youtube.com/channel/UC0rZoXAD5lxgBHMsjrGwWWQ"
    assert (
        handler.sanitize_source_url(url2)
        == "https://www.youtube.com/channel/UC0rZoXAD5lxgBHMsjrGwWWQ"
    )

    url3 = "https://youtube.com/playlist?list=PLC0nd42SBTaMs6EEvESEfopfFJZjRqYmA"
    assert (
        handler.sanitize_source_url(url3)
        == "https://www.youtube.com/playlist?list=PLC0nd42SBTaMs6EEvESEfopfFJZjRqYmA"
    )

    with pytest.raises(InvalidSourceUrl):
        handler.sanitize_source_url(url="https://www.youtube.com/xxxxxxxxxxxxxxxx")

    with pytest.raises(InvalidSourceUrl):
        handler.get_channel_url_from_channel_name_id_url(
            url="https://www.youtube.com/xxxxxxxxxxxxxxxx"
        )

    with pytest.raises(InvalidSourceUrl):
        handler.get_channel_url_from_channel_url(url="https://www.youtube.com/xxxxxxxxxxxxxxxx")

    with pytest.raises(InvalidSourceUrl):
        handler.get_playlist_url_from_playlist_url(url="https://www.youtube.com/xxxxxxxxxxxxxxxx")


def test_get_video_ydl_opts(handler: Handler) -> None:
    """
    Test get_video_ydl_opts function.
    """
    assert handler.get_video_ydl_opts() == {
        "format": "worst[ext=mp4]",
        "skip_download": True,
        "simulate": True,
        "ignore_no_formats_error": False,
        "no_color": True,
    }


async def test_get_source_info_dict_kwargs(handler: Handler) -> None:
    """
    Test get_source_info_dict_kwargs function.
    """
    # Test url with '/c/' in it
    url = "https://www.youtube.com/channel/UC0rZoXAD5lxgBHMsjrGwWWQ"
    result = await handler.get_source_info_dict_kwargs(url)
    assert result == {
        "extract_flat": True,
        "playlistreverse": True,
        "playlistend": handler.YDL_OPT_PLAYLISTEND,
        "dateafter": handler.YDL_OPT_DATEAFTER,
    }

    # Test url with '/user/' in it
    url = "https://www.youtube.com/playlist?list=PLC0nd42SBTaMs6EEvESEfopfFJZjRqYmA"
    result = await handler.get_source_info_dict_kwargs(url)
    assert result == {
        "extract_flat": True,
        "playlistreverse": False,
        "playlistend": 100,
        "dateafter": "now-20y",
    }

    # Test url with neither '/c/' nor '/user/' in it
    url = "https://www.youtube.com/v123456"
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

    # Handle playlist
    mocked_source_info_dict["metadata"][
        "url"
    ] = "https://www.youtube.com/playlist?list=PLC0nd42SBTaMs6EEvESEfopfFJZjRqYmA"
    data["logo"] = f"/static/logos/nSzvWjcx.png"
    data["ordered_by"] = "created_at"
    data["url"] = "https://www.youtube.com/playlist?list=PLC0nd42SBTaMs6EEvESEfopfFJZjRqYmA"
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
    mocked_source_info_dict.pop("thumbnails")
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

    # Test Playlist


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


async def test_map_video_info_dict_entity_to_video_dict_errors(
    handler: Handler, mocked_source: dict[str, Any], mocked_entry_info_dict: dict[str, Any]
) -> None:
    # video = mocked_source["videos"][0]
    entry_info_dict = mocked_entry_info_dict.copy()

    with pytest.raises(Http410Error):
        handler.map_video_info_dict_entity_to_video_dict(entry_info_dict={})

    with pytest.raises(IsPrivateVideoError):
        entry_info_dict["title"] = "[Private video]"
        handler.map_video_info_dict_entity_to_video_dict(entry_info_dict=entry_info_dict)

    with pytest.raises(IsDeletedVideoError):
        entry_info_dict["title"] = "[Deleted video]"
        handler.map_video_info_dict_entity_to_video_dict(entry_info_dict=entry_info_dict)

    with pytest.raises(FormatNotFoundError):
        entry_info_dict = mocked_entry_info_dict.copy()
        entry_info_dict["formats"][0]["url"] = ".m3u8"
        handler.map_video_info_dict_entity_to_video_dict(entry_info_dict=entry_info_dict)


async def test_map_video_info_dict_entity_to_video_dict_format_id_keyerror(
    handler: Handler, mocked_entry_info_dict: dict[str, Any]
) -> None:
    with pytest.raises(FormatNotFoundError):
        entry_info_dict = mocked_entry_info_dict.copy()
        entry_info_dict.pop("format_id")
        handler.map_video_info_dict_entity_to_video_dict(entry_info_dict=entry_info_dict)

    with pytest.raises(KeyError):
        entry_info_dict = mocked_entry_info_dict.copy()
        entry_info_dict.pop("formats")
        handler.map_video_info_dict_entity_to_video_dict(entry_info_dict=entry_info_dict)


def test_get_ordered_by(handler: Handler) -> None:
    assert (
        handler.get_ordered_by(
            url="https://www.youtube.com/playlist?list=PLC0nd42SBTaMs6EEvESEfopfFJZjRqYmA"
        )
        == SourceOrderBy.CREATED_AT.value
    )
    assert (
        handler.get_ordered_by(url="https://www.youtube.com/@Styxhexenhammer666")
        == SourceOrderBy.RELEASED_AT.value
    )
