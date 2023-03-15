from typing import Any

import asyncio

from loguru import logger as _logger
from sqlmodel import Session

from app import crud, logger, models
from app.handlers import get_handler_from_url
from app.models.source import Source, SourceCreate
from app.models.video import Video, VideoCreate
from app.paths import LOGOS_PATH
from app.services.feed import build_rss_file
from app.services.logo import create_logo_from_text
from app.services.video import get_videos_needing_refresh, refresh_videos
from app.services.ytdlp import get_info_dict

fetch_logger = _logger.bind(name="fetch_logger")


async def get_source_info_dict(
    source_id: str | None,
    url: str,
    extract_flat: bool | None = None,
    playlistreverse: bool | None = None,
    playlistend: int | None = None,
    dateafter: str | None = None,
    reverse_import_order: bool = False,
) -> dict[str, Any]:
    """
    Retrieve the info_dict from yt-dlp for a Source

    Parameters:
        source_id (Union[str, None]): An optional ID for the source. If not provided,
            a unique ID will be generated from the URL.
        url (str | None): The URL of the Source
        extract_flat (bool | None): Whether to extract a flat list of videos in the playlist.
        playlistreverse (bool | None): Whether to reverse the playlist.
        playlistend (int | None): The index of the last video to extract.
        dateafter (str | None): The date after which to extract videos.
        reverse_import_order (bool): Whether to reverse the order of the videos in the playlist.

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

    # Get source_info_dict_kwargs from handler
    source_info_dict_kwargs = await handler.get_source_info_dict_kwargs(url=url)

    # Get playlistreverse from handler or kwargs
    playlistreverse = playlistreverse or source_info_dict_kwargs["playlistreverse"]

    # Reverse they playlistreverse if reverse_import_order is True
    playlistreverse = not playlistreverse if reverse_import_order else playlistreverse

    # Get ydl_opts from handler
    ydl_opts = handler.get_source_ydl_opts(
        extract_flat=extract_flat or source_info_dict_kwargs["extract_flat"],
        playlistreverse=playlistreverse,
        playlistend=playlistend or source_info_dict_kwargs["playlistend"],
        dateafter=dateafter or source_info_dict_kwargs["dateafter"],
    )
    custom_extractors = handler.YTDLP_CUSTOM_EXTRACTORS or []

    # Build source_info_dict
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
    source_info_dict: dict[str, Any], created_by_user_id: str
) -> SourceCreate:
    """
    Get a `Source` object from a source_info_dict.

    Parameters:
        source_info_dict (dict): The source_info_dict.
        created_by (str): user_id of authenticated user.

    Returns:
        SourceCreate: The `SourceCreate` object.
    """
    handler = get_handler_from_url(url=source_info_dict["metadata"]["url"])
    source_videos = get_source_videos_from_source_info_dict(source_info_dict=source_info_dict)
    return SourceCreate(
        created_by=created_by_user_id,
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

    if len(entries) > 0 and entries[0]["_type"] == "playlist":
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

            db_video = await crud.video.get_or_none(db=db, id=new_video.id)
            if not db_video:
                try:
                    db_video = await crud.video.create(obj_in=new_video, db=db)
                except crud.RecordAlreadyExistsError:
                    db_video = await crud.video.get(db=db, id=new_video.id)

            db_source.videos.append(db_video)

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


async def fetch_source(db: Session, id: str, ignore_video_refresh=False) -> models.FetchResults:
    """
    Fetch new data from yt-dlp for the source and update the source in the database.

    This function will also delete any videos that are no longer associated with the source.

    Args:
        id: The id of the source to fetch and update.
        db (Session): The database session.
        ignore_video_refresh: If True, do not refresh videos.

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
        reverse_import_order=db_source.reverse_import_order,
    )
    _source = await get_source_from_source_info_dict(
        source_info_dict=source_info_dict, created_by_user_id=db_source.created_by
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
    videos_needing_refresh = (
        get_videos_needing_refresh(videos=db_source.videos) if not ignore_video_refresh else []
    )
    refreshed_videos = await refresh_videos(
        videos_needing_refresh=videos_needing_refresh,
        db=db,
    )

    # Check if source needs a logo
    if db_source.logo and "static/logos" in db_source.logo:
        logo_path = LOGOS_PATH / f"{db_source.id}.png"
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
