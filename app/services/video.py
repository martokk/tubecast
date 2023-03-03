from typing import Any

import asyncio
from datetime import datetime, timedelta

from sqlmodel import Session
from yt_dlp.utils import YoutubeDLError

from app import crud, logger, models
from app.core.notify import notify
from app.handlers import get_handler_from_url
from app.services.ytdlp import Http410Error, IsLiveEventError, IsPrivateVideoError, get_info_dict


async def get_video_info_dict(
    url: str,
) -> dict[str, Any]:  # sourcery skip: inline-immediately-returned-variable
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
    info_dict = get_info_dict(url=url, ydl_opts=ydl_opts, custom_extractors=custom_extractors)

    # Save Pickle
    # cache_file.parent.mkdir(exist_ok=True, parents=True)
    # cache_file.write_bytes(pickle.dumps(info_dict))
    return await info_dict


def get_video_from_video_info_dict(
    video_info_dict: dict[str, Any], source_id: str
) -> models.VideoCreate:
    handler = get_handler_from_url(url=video_info_dict["webpage_url"])
    video_dict = handler.map_video_info_dict_entity_to_video_dict(entry_info_dict=video_info_dict)
    video_dict["source_id"] = source_id
    return models.VideoCreate(**video_dict)


async def refresh_all_videos(older_than_hours: int, db: Session) -> list[models.Video]:
    """
    Fetches new data from yt-dlp for all Videos that are older than a certain number of hours.

    Args:
        older_than_hours: The minimum age of the videos to refresh, in hours.
        db (Session): The database session.

    Returns:
        The refreshed list of videos.
    """
    videos = await crud.video.get_all(db=db) or []
    videos_needing_refresh = get_videos_needing_refresh(
        videos=videos, older_than_hours=older_than_hours
    )
    return await refresh_videos(videos_needing_refresh=videos_needing_refresh, db=db)


async def fetch_video(video_id: str, db: Session) -> models.Video:
    """Fetches new data from yt-dlp for the video.

    Args:
        video_id: The ID of the video to fetch data for.
        db (Session): The database session.

    Returns:
        The updated video.
    """
    # Get the video from the database
    db_video = await crud.video.get(id=video_id, db=db)
    source_id = db_video.source_id

    # Fetch video information from yt-dlp and create the video object
    video_info_dict = await get_video_info_dict(url=db_video.url)
    _video = get_video_from_video_info_dict(video_info_dict=video_info_dict, source_id=source_id)

    # Update the video in the database and return it
    return await crud.video.update(obj_in=models.VideoUpdate(**_video.dict()), id=_video.id, db=db)


async def fetch_all_videos(db: Session) -> list[models.Video]:
    """
    Fetch videos from all sources.

    Args:
        db (Session): The database session.

    Returns:
        List[Video]: List of fetched videos
    """
    logger.debug("Fetching ALL Videos...")
    videos = await crud.video.get_all(db=db) or []
    fetched = []
    for _video in videos:
        fetched.append(await fetch_video(video_id=_video.id, db=db))

    return fetched


async def fetch_videos(videos: list[models.Video], db: Session) -> list[models.Video]:
    """
    Fetches new data for a list of videos from yt-dlp.
    Ignores videos that are live events.

    Args:
        videos: The list of videos to fetch.
        db (Session): The database session.

    Returns:
        The fetched list of videos.
    """
    fetched_videos = []
    for video in videos:
        try:
            fetched_video = await fetch_video(video_id=video.id, db=db)
        except IsLiveEventError:
            continue
        except (Http410Error, IsPrivateVideoError):
            # Video has been deleted on host server
            await crud.video.remove(db=db, id=video.id)
            continue
        except (YoutubeDLError, Exception) as e:
            err_msg = f"Error fetching video: \n{e=} \n{video=}"
            logger.critical(err_msg)
            await notify(telegram=True, email=False, text=err_msg)
            continue

        # Allow other tasks to run
        await asyncio.sleep(0)

        fetched_videos.append(fetched_video)

    return fetched_videos


async def refresh_videos(
    videos_needing_refresh: list[models.Video], db: Session
) -> list[models.Video]:
    """
    Fetches new data from yt-dlp for videos that meet all criteria.

    Args:
        videos_needing_refresh: The list of videos to refresh.
        db (Session): The database session.

    Returns:
        The refreshed list of videos.
    """
    sorted_videos_needing_refresh = sort_videos_by_updated_at(videos=videos_needing_refresh)
    return await fetch_videos(videos=sorted_videos_needing_refresh, db=db)


def get_videos_needing_refresh(
    videos: list[models.Video], older_than_hours: int
) -> list[models.Video]:
    """
    Gets a list of videos that meet all criteria.

    Args:
        videos: The list of videos to refresh.
        older_than_hours: The minimum age of the videos to refresh, in hours.

    Returns:
        The refreshed list of videos.
    """
    age_threshold = datetime.utcnow() - timedelta(hours=older_than_hours)
    return [
        video
        for video in videos
        if (
            video.updated_at < age_threshold or video.released_at is None or video.media_url is None
        )
    ]


def sort_videos_by_updated_at(videos: list[models.Video]) -> list[models.Video]:
    """
    Sorts a list of videos by the `updated_at` property.

    Args:
        videos: The list of videos to sort.

    Returns:
        The sorted list of videos.
    """
    return sorted(videos, key=lambda video: video.updated_at, reverse=False)
