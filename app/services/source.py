from typing import Any

import asyncio

from loguru import logger as _logger
from sqlmodel import Session

from app import crud, handlers, logger, models, settings
from app.handlers import get_handler_from_url
from app.models.source import Source, SourceCreate
from app.models.video import Video, VideoCreate
from app.services.feed import build_rss_file
from app.services.video import get_videos_needing_refresh, refresh_videos
from app.services.ytdlp import get_info_dict

fetch_logger = _logger.bind(name="fetch_logger")


async def get_source_info_dict(
    source_id: str | None,
    url: str,
    extract_flat: bool,
    playlistreverse: bool,
    playlistend: int,
    dateafter: str,
) -> dict[str, Any]:
    """
    Retrieve the info_dict from yt-dlp for a Source

    Parameters:
        source_id (Union[str, None]): An optional ID for the source. If not provided,
            a unique ID will be generated from the URL.
        url (str): The URL of the Source
        extract_flat (bool): Whether to extract a flat list of videos in the playlist.
        playlistreverse (bool): Whether to reverse the playlist.
        playlistend (int): The index of the last video to extract.
        dateafter (str): The date after which to extract videos.

    Returns:
        dict: The info dictionary for the Source

    """
    # source_id = source_id or await generate_source_id_from_url(url=url)
    # cache_file = Path(SOURCE_INFO_CACHE_PATH / source_id)

    # # Load Cache
    # if use_cache and cache_file.exists():
    #     return pickle.loads(cache_file.read_bytes())

    # Get info_dict from yt-dlp
    handler = get_handler_from_url(url=url)
    ydl_opts = handler.get_source_ydl_opts(
        extract_flat=extract_flat,
        playlistreverse=playlistreverse,
        playlistend=playlistend,
        dateafter=dateafter,
    )
    custom_extractors = handler.YTDLP_CUSTOM_EXTRACTORS or []
    _source_info_dict = await get_info_dict(
        url=url,
        ydl_opts=ydl_opts,
        custom_extractors=custom_extractors,
        # ie_key="CustomRumbleChannel",
    )
    _source_info_dict["source_id"] = source_id

    # Save Pickle
    # cache_file.write_bytes(pickle.dumps(_source_info_dict))
    return _source_info_dict


async def get_source_from_source_info_dict(
    source_info_dict: dict[str, Any], user_id: str
) -> SourceCreate:
    """
    Get a `Source` object from a source_info_dict.

    Parameters:
        source_info_dict (dict): The source_info_dict.
        user_id (str): user_id of authenticated user.

    Returns:
        SourceCreate: The `SourceCreate` object.
    """
    handler = get_handler_from_url(url=source_info_dict["metadata"]["url"])
    source_videos = get_source_videos_from_source_info_dict(source_info_dict=source_info_dict)
    return SourceCreate(
        created_by=user_id,
        **handler.map_source_info_dict_to_source_dict(
            source_info_dict=source_info_dict, source_videos=source_videos
        ),
    )


def get_source_videos_from_source_info_dict(source_info_dict: dict[str, Any]) -> list[VideoCreate]:
    """
    Get a list of `Video` objects from a source_info_dict.

    Parameters:
        source_info_dict (dict): The source_info_dict.

    Returns:
        list: The list of `Video` objects.
    """
    handler = get_handler_from_url(url=source_info_dict["metadata"]["url"])
    entries = source_info_dict["entries"]

    if len(entries) > 0 and entries[0].get("entries"):
        playlists = entries
    else:
        playlists = [source_info_dict]

    video_dicts = [
        handler.map_source_info_dict_entity_to_video_dict(
            source_id=source_info_dict["source_id"], entry_info_dict=entry_info_dict
        )
        for playlist in playlists
        for entry_info_dict in playlist.get("entries", [])
        if entry_info_dict.get("live_status") is None
    ]
    return [VideoCreate(**video_dict) for video_dict in video_dicts]


async def add_new_source_videos_from_fetched_videos(
    fetched_videos: list[VideoCreate], db_source: Source, db: Session
) -> list[VideoCreate]:
    """
    Add new videos from a list of fetched videos to a source in the database.

    Args:
        fetched_videos: A list of Video objects fetched from a source.
        db_source: The Source object in the database to add the new videos to.
        db (Session): The database session.

    Returns:
        A list of Video objects that were added to the database.
    """
    db_video_ids = [video.id for video in db_source.videos]

    # Add videos that were fetched, but not in the database.
    added_videos = []
    for fetched_video in fetched_videos:
        if fetched_video.id not in db_video_ids:
            new_video = VideoCreate(**fetched_video.dict())
            added_videos.append(new_video)
            await crud.video.create(obj_in=new_video, db=db)

    return added_videos


async def delete_orphaned_source_videos(
    fetched_videos: list[Video], db_source: Source, db: Session
) -> list[Video]:
    """
    Delete videos that are no longer present in `fetched_videos`.

    Args:
        fetched_videos: The list of Videos to compare the videos against.
        db_source: The source object in the database to delete videos from.
        db (Session): The database session.

    Returns:
        The list of deleted Videos.
    """
    fetched_video_ids = [video.id for video in fetched_videos]

    # Iterate through the videos in the source in the database
    deleted_videos = []
    for db_video in db_source.videos:
        if db_video.id not in fetched_video_ids:
            deleted_videos.append(db_video)
            await crud.video.remove(id=db_video.id, db=db)

    return deleted_videos


async def fetch_source(db: Session, id: str) -> models.FetchResults:
    """
    Fetch new data from yt-dlp for the source and update the source in the database.

    This function will also delete any videos that are no longer associated with the source.

    Args:
        id: The id of the source to fetch and update.
        db (Session): The database session.

    Returns:
        models.FetchResult: The result of the fetch.
    """

    db_source = await crud.source.get(id=id, db=db)

    info_message = f"Fetching Source(id='{db_source.id}, name='{db_source.name}')"
    logger.info(info_message)
    fetch_logger.info(info_message)

    # Fetch source information from yt-dlp and create the source object
    source_info_dict = await get_source_info_dict(
        source_id=id,
        url=db_source.url,
        extract_flat=True,
        playlistreverse=True,
        playlistend=settings.BUILD_FEED_RECENT_VIDEOS,
        dateafter=settings.BUILD_FEED_DATEAFTER,
    )
    _source = await get_source_from_source_info_dict(
        source_info_dict=source_info_dict, user_id=db_source.created_by
    )
    db_source = await crud.source.update(obj_in=models.SourceUpdate(**_source.dict()), id=id, db=db)

    # Use the source information to fetch the videos
    fetched_videos = get_source_videos_from_source_info_dict(source_info_dict=source_info_dict)

    # Add new videos to database
    new_videos = await add_new_source_videos_from_fetched_videos(
        fetched_videos=fetched_videos, db_source=db_source, db=db
    )

    # Delete orphaned videos from database
    deleted_videos: list[models.Video] = []
    # NOTE: Enable if db grows too large. Otherwise best not to delete any videos
    # from database as podcast app will still reference the video's feed_media_url
    # deleted_videos = await delete_orphaned_source_videos(
    #     fetched_videos=fetched_videos, db_source=db_source
    # )

    # Refresh existing videos in database
    handler = handlers.get_handler_from_string(handler_string=db_source.handler)
    videos_needing_refresh = get_videos_needing_refresh(
        videos=db_source.videos, older_than_hours=handler.MAX_VIDEO_AGE_HOURS
    )
    refreshed_videos = await refresh_videos(
        videos_needing_refresh=videos_needing_refresh,
        db=db,
    )

    # Build RSS File
    await build_rss_file(source=db_source)

    success_message = (
        f"Completed fetching Source(id='{db_source.id}', name='{db_source.name}'). "
        f"[{len(new_videos)}/{len(deleted_videos)}/{len(refreshed_videos)}] "
        f"Added {len(new_videos)} new videos. "
        f"Deleted {len(deleted_videos)} orphaned videos. "
        f"Refreshed {len(refreshed_videos)} videos."
    )
    logger.success(success_message)
    fetch_logger.success(success_message)

    return models.FetchResults(
        sources=1,
        added_videos=len(new_videos),
        deleted_videos=len(deleted_videos),
        refreshed_videos=len(refreshed_videos),
    )


async def fetch_all_sources(db: Session) -> models.FetchResults:
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
    results = models.FetchResults()

    for _source in sources:
        source_fetch_results = await fetch_source(id=_source.id, db=db)
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
