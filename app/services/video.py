from typing import Any

from app.handlers import get_handler_from_url
from app.models import Video, VideoCreate
from app.services.ytdlp import get_info_dict


async def get_video_info_dict(
    url: str,
) -> dict[str, Any]:  # sourcery skip: inline-immediately-returned-variable
    """
    Retrieve the info_dict for a Video.

    Parameters:
        url (str): The URL of the video.

    Returns:
        dict: The info dictionary for the video.
    """
    # Get info_dict from yt-dlp
    handler = get_handler_from_url(url=url)

    if handler.DISABLED:
        raise Exception("Source is DISABLED in settings.")

    ydl_opts = handler.get_video_ydl_opts()
    custom_extractors = handler.YTDLP_CUSTOM_EXTRACTORS
    info_dict = await get_info_dict(url=url, ydl_opts=ydl_opts, custom_extractors=custom_extractors)
    return info_dict


def get_video_from_video_info_dict(video_info_dict: dict[str, Any]) -> VideoCreate:
    """
    Get a VideoCreate object from a video info_dict.

    Args:
        video_info_dict: The video info_dict.

    Returns:
        The VideoCreate object.
    """
    handler = get_handler_from_url(url=video_info_dict["webpage_url"])
    video_dict = handler.map_video_info_dict_entity_to_video_dict(entry_info_dict=video_info_dict)
    return VideoCreate(**video_dict)


def sort_videos_by_updated_at(videos: list[Video]) -> list[Video]:
    """
    Sorts a list of videos by the `updated_at` property.

    Args:
        videos: The list of videos to sort.

    Returns:
        The sorted list of videos.
    """
    return sorted(videos, key=lambda video: video.updated_at, reverse=False)
