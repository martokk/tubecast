from typing import Any

from datetime import datetime, timedelta

from sqlmodel import Session

from tubecast import crud, settings
from tubecast.handlers import get_handler_from_url
from tubecast.models.video import Video, VideoCreate
from tubecast.services.ytdlp import get_info_dict


async def get_video_info_dict(
    url: str,
) -> dict[str, Any]:
    """
    Retrieve the info_dict for a Video.

    This function first checks if a cached version of the info dictionary is available,
    and if it is, it returns that. Otherwise, it uses YouTube-DL to retrieve the
    info dictionary and then stores it in the cache for future use.

    Parameters:
        url (str): The URL of the video.


    Returns:
        dict: The info dictionary for the video.
    """
    # video_id = generate_video_id_from_url(url=url)
    # cache_file = Path(VIDEO_INFO_CACHE_PATH / f"{video_id}.pickle")

    # Load Cache
    # if use_cache and cache_file.exists():
    #     return pickle.loads(cache_file.read_bytes())

    # Get info_dict from yt-dlp
    handler = get_handler_from_url(url=url)
    ydl_opts = handler.get_video_ydl_opts()
    custom_extractors = handler.YTDLP_CUSTOM_EXTRACTORS
    info_dict = await get_info_dict(url=url, ydl_opts=ydl_opts, custom_extractors=custom_extractors)

    # Save Pickle
    # cache_file.parent.mkdir(exist_ok=True, parents=True)
    # cache_file.write_bytes(pickle.dumps(info_dict))
    return info_dict


async def get_video_from_video_info_dict(
    video_info_dict: dict[str, Any], source_id: str
) -> VideoCreate:
    handler = get_handler_from_url(url=video_info_dict["webpage_url"])
    video_dict = handler.map_video_info_dict_entity_to_video_dict(entry_info_dict=video_info_dict)
    video_dict["source_id"] = source_id
    return VideoCreate(**video_dict)


async def refresh_all_videos(older_than_hours: int, db: Session) -> list[Video]:
    """
    Fetches new data from yt-dlp for all Videos that are older than a certain number of hours.

    Args:
        older_than_hours: The minimum age of the videos to refresh, in hours.
        db (Session): The database session.

    Returns:
        The refreshed list of videos.
    """
    videos = await crud.video.get_all(db=db) or []
    return await refresh_videos(videos=videos, older_than_hours=older_than_hours, db=db)


async def fetch_videos(videos: list[Video], db: Session) -> list[Video]:
    """
    Fetches new data for a list of videos from yt-dlp.

    Args:
        videos: The list of videos to fetch.
        db (Session): The database session.

    Returns:
        The fetched list of videos.
    """
    return [await crud.video.fetch_video(video_id=video.id, db=db) for video in videos]


async def refresh_videos(
    videos: list[Video], db: Session, older_than_hours: int = settings.MAX_VIDEO_AGE_HOURS
) -> list[Video]:
    """
    Fetches new data from yt-dlp for videos that meet all criteria.

    Args:
        videos: The list of videos to refresh.
        older_than_hours: The minimum age of the videos to refresh, in hours.
        db (Session): The database session.

    Returns:
        The refreshed list of videos.
    """
    age_threshold = datetime.utcnow() - timedelta(hours=older_than_hours)
    videos_needing_refresh = [
        video
        for video in videos
        if (
            video.updated_at < age_threshold or video.released_at is None or video.media_url is None
        )
    ]
    sorted_videos_needing_refresh = await sort_videos_by_updated_at(videos=videos_needing_refresh)
    return await fetch_videos(videos=sorted_videos_needing_refresh, db=db)


async def sort_videos_by_updated_at(videos: list[Video]) -> list[Video]:
    """
    Sorts a list of videos by the `updated_at` property.

    Args:
        videos: The list of videos to sort.

    Returns:
        The sorted list of videos.
    """
    return sorted(videos, key=lambda video: video.updated_at, reverse=False)
