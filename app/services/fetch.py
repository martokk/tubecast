"""
Note:
    - "Fetch" forces a fetch, even if not due for a fetch.
    - "Refresh" only fetches videos that are due for a fetch.
"""

import asyncio
from datetime import datetime, timedelta

from loguru import logger as _logger
from sqlmodel import Session
from yt_dlp.utils import YoutubeDLError

from app import crud, logger, paths
from app.core.notify import notify
from app.handlers import get_handler_from_string
from app.models import FetchResults, Source, SourceUpdate, Video, VideoUpdate
from app.services.feed import build_rss_file
from app.services.logo import create_logo_from_text
from app.services.source import (
    add_new_source_info_dict_videos_to_source,
    get_source_from_source_info_dict,
    get_source_info_dict,
)
from app.services.video import (
    get_video_from_video_info_dict,
    get_video_info_dict,
    sort_videos_by_updated_at,
)
from app.services.ytdlp import (
    AccountNotFoundError,
    Http410Error,
    IsDeletedVideoError,
    IsLiveEventError,
    IsPrivateVideoError,
    VideoUnavailableError,
)

fetch_logger = _logger.bind(name="fetch_logger")


class FetchError(Exception):
    """
    Base class for fetch errors.
    """


class FetchCanceledError(FetchError):
    """
    Raised when a fetch is cancelled.
    """


class FetchVideoError(FetchError):
    """
    Raised when a video fetch fails.
    """


class FetchSourceError(FetchError):
    """
    Raised when a source fetch fails.
    """


async def log_and_notify(message: str) -> None:
    """
    Log and notify a message.

    Args:
        message (str): The message to log and notify.
    """
    logger.critical(message)
    await notify(telegram=True, email=False, text=message)


async def fetch_all_sources(db: Session) -> FetchResults:
    """
    Fetch all sources.

    Args:
        db (Session): The database session.

    Returns:
        models.FetchResults: The results of the fetch.
    """
    logger.info("Fetching ALL Sources...")
    fetch_logger.info("Fetching ALL Sources...")
    sources = await crud.source.get_all(db=db) or []
    results = FetchResults()

    for _source in sources:
        if _source.is_deleted or _source.is_active is False:
            continue
        try:
            source_fetch_results = await fetch_source(id=_source.id, db=db)
        except FetchCanceledError:
            continue

        results += source_fetch_results

        # Allow other tasks to run
        await asyncio.sleep(0)

    success_message = (
        f"Completed fetching All ({results.sources}) Sources. "
        f"[{results.added_videos}/{results.deleted_videos}/{results.refreshed_videos}]"
        f"Added {results.added_videos} new videos. "
        f"Deleted {results.deleted_videos} orphaned videos. "
        f"Refreshed {results.refreshed_videos} videos.\n"
    )
    logger.success(success_message)
    fetch_logger.success(success_message)

    return results


async def fetch_source(db: Session, id: str, ignore_video_refresh: bool = False) -> FetchResults:
    """
    Fetch new data from yt-dlp for the source and update the source in the database.

    This function will also delete any videos that are no longer associated with the source.

    Args:
        db (Session): The database session.
        id: The id of the source to fetch and update.
        ignore_video_refresh: If True, do not refresh videos.

    Returns:
        models.FetchResult: The result of the fetch.
    """

    db_source = await crud.source.get(id=id, db=db)

    info_message = f"Fetching Source(id='{db_source.id}, name='{db_source.name}')"
    logger.info(info_message)
    fetch_logger.info(info_message)

    # Fetch source information from yt-dlp and create the source object
    try:
        source_info_dict = await get_source_info_dict(
            source_id=id,
            url=db_source.url,
            reverse_import_order=db_source.reverse_import_order,
        )
    except AccountNotFoundError as e:
        await log_and_notify(message=f"AccountNotFoundError: \n{e=} \n{db_source=}")
        await handle_source_is_deleted(db=db, source_id=id, error_message=str(e))
        raise FetchCanceledError from e

    # Update source in database
    _source = await get_source_from_source_info_dict(
        source_info_dict=source_info_dict,
        created_by_user_id=db_source.created_by,
        reverse_import_order=db_source.reverse_import_order,
        source_name=db_source.name,
    )
    db_source = await crud.source.update(obj_in=SourceUpdate(**_source.dict()), id=id, db=db)

    # Use source_info_dict to add new videos to the Source
    new_videos = await add_new_source_info_dict_videos_to_source(
        db=db, source_info_dict=source_info_dict, db_source=db_source
    )

    # Delete orphaned videos from database
    deleted_videos: list[Video] = []
    # NOTE: Enable if db grows too large. Otherwise best not to delete any videos
    # from database as podcast app will still reference the video's feed_media_url
    # deleted_videos = await delete_orphaned_source_videos(
    #     fetched_videos=fetched_videos, db_source=db_source
    # )

    # Refresh existing videos in database
    refreshed_videos = await refresh_videos(
        videos=db_source.videos,
        db=db,
    )

    # Check if source needs a logo
    if db_source.logo and "static/logos" in db_source.logo:
        logo_path = paths.LOGOS_PATH / f"{db_source.id}.png"
        if not logo_path.exists():
            create_logo_from_text(text=db_source.name, file_path=logo_path)

    # Build RSS Files
    await build_rss_file(source=db_source)
    for filter in db_source.filters:
        await build_rss_file(filter=filter)

    success_message = (
        f"Completed fetching Source(id='{db_source.id}', name='{db_source.name}'). "
        f"[{len(new_videos)}/{len(deleted_videos)}/{len(refreshed_videos)}] "
        f"Added {len(new_videos)} new videos. "
        f"Deleted {len(deleted_videos)} orphaned videos. "
        f"Refreshed {len(refreshed_videos)} videos."
    )
    logger.success(success_message)
    fetch_logger.success(success_message)

    return FetchResults(
        sources=1,
        added_videos=len(new_videos),
        deleted_videos=len(deleted_videos),
        refreshed_videos=len(refreshed_videos),
    )


async def handle_source_is_deleted(db: Session, source_id: str, error_message: str) -> Source:
    """
    Handle when a source has been Deleted by Source Provider (Youtube, Rumble, etc.)

    Args:
        db (Session): The database session.
        source_id (str): The source's id.
        last_fetch_error (str): The error message.

    Returns:
        updated_source (models.Source): The updated source.
    """
    return await crud.source.update(
        db=db,
        id=source_id,
        obj_in=SourceUpdate(
            is_active=False,
            is_deleted=True,
            last_fetch_error=error_message,
        ),
    )


async def fetch_all_videos(db: Session) -> list[Video]:
    """
    Fetch videos for all sources.
    This will force a fetch for all videos, even if they are not due for a fetch.
    It's recommended to use `refresh_all_videos` instead.

    Args:
        db (Session): The database session.

    Returns:
        List[Video]: List of fetched videos
    """
    logger.warning("Fetching ALL Videos...")
    logger.warning(
        "NOTE: This forces a fetch for all videos, even if they are not due for a fetch."
    )
    logger.warning("It's recommended to use `refresh_all_videos` instead")
    videos = await crud.video.get_all(db=db) or []
    fetched = []
    for _video in videos:
        try:
            fetched_video = await fetch_video(video_id=_video.id, db=db)
        except (FetchVideoError, FetchCanceledError):
            continue

        fetched.append(fetched_video)

    return fetched


async def fetch_videos(videos: list[Video], db: Session) -> list[Video]:
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
        except (FetchVideoError, FetchCanceledError):
            continue

        # Allow other tasks to run
        await asyncio.sleep(0)

        fetched_videos.append(fetched_video)

    return fetched_videos


async def fetch_video(video_id: str, db: Session) -> Video:
    """Fetches new data from yt-dlp for the video.

    Args:
        video_id: The ID of the video to fetch data for.
        db (Session): The database session.

    Returns:
        The updated video.
    """
    # Get the video from the database
    db_video = await crud.video.get(id=video_id, db=db)

    # Fetch video information from yt-dlp and create the video object
    try:
        video_info_dict = await get_video_info_dict(url=db_video.url)

    except crud.RecordNotFoundError as e:
        await log_and_notify(message=f"Database error: Video not found: \n{db_video=}")
        raise e

    except (
        VideoUnavailableError,
        Http410Error,
        IsPrivateVideoError,
        IsDeletedVideoError,
        IsLiveEventError,
        YoutubeDLError,
    ) as e:
        await handle_unavailable_video(db=db, video_id=video_id, error_message=str(e))

        # If the video was created more than 36 hours ago, raise an error
        if db_video.created_at < datetime.utcnow() - timedelta(hours=36):
            await log_and_notify(message=f"FetchVideoError: \n{e=} \n{db_video=}")
            raise FetchVideoError(e) from e

        raise FetchCanceledError from e

    except (YoutubeDLError, Exception) as e:
        await log_and_notify(message=f"Error fetching video: \n{e=} \n{db_video=}")
        raise e

    _video = get_video_from_video_info_dict(video_info_dict=video_info_dict)

    # Update the video in the database and return it
    return await crud.video.update(obj_in=VideoUpdate(**_video.dict()), id=_video.id, db=db)


async def handle_unavailable_video(db: Session, video_id: str, error_message: str) -> None:
    """
    Handle when a video is unavailable.

    Args:
        db (Session): The database session.
        video_id (str): The video_id
        error_message (str): The error message.

    """
    # If the video is unavailable, delete it from the database
    return await crud.video.remove(db=db, id=video_id)


def get_videos_needing_refresh(videos: list[Video]) -> list[Video]:
    """
    Gets a list of videos that meet all criteria.

    Args:
        videos: The list of videos to refresh.

    Returns:
        The refreshed list of videos.
    """
    videos_needing_refresh = []
    for video in videos:
        if "private" in str(video.title).lower() or "deleted" in str(video.title).lower():
            continue
        handler = get_handler_from_string(handler_string=video.handler)
        updated_at_threshold = datetime.utcnow() - timedelta(
            hours=handler.REFRESH_UPDATE_INTERVAL_HOURS
        )
        released_recently_threshold = datetime.utcnow() - timedelta(
            days=handler.REFRESH_RELEASED_RECENT_DAYS
        )

        missing_required_data = video.media_url is None or not video.released_at
        expired_data = video.updated_at < updated_at_threshold
        recently_released = (
            True if not video.released_at else video.released_at > released_recently_threshold
        )

        needs_refresh = expired_data and recently_released
        if missing_required_data or needs_refresh:
            videos_needing_refresh.append(video)

    return videos_needing_refresh


async def refresh_all_videos(db: Session) -> list[Video]:
    """
    If a video has expired data, fetches new data from yt-dlp.

    Args:
        db (Session): The database session.

    Returns:
        The refreshed list of videos.
    """
    videos = await crud.video.get_all(db=db) or []
    return await refresh_videos(videos=videos, db=db)


async def refresh_videos(videos: list[Video], db: Session) -> list[Video]:
    """
    If a video has expired data, fetches new data from yt-dlp.

    Args:
        videos: The list of videos to refresh.
        db (Session): The database session.

    Returns:
        The refreshed list of videos.
    """
    videos_needing_refresh = get_videos_needing_refresh(videos=videos)
    sorted_videos_needing_refresh = sort_videos_by_updated_at(videos=videos_needing_refresh)
    return await fetch_videos(videos=sorted_videos_needing_refresh, db=db)
