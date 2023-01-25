from typing import Any

from sqlmodel import Session

from tubecast import crud
from tubecast.handlers import get_handler_from_url
from tubecast.models.source import Source, SourceCreate
from tubecast.models.video import Video, VideoCreate
from tubecast.services.ytdlp import get_info_dict


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
        playlistreverse=playlistend,
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
    source_videos = await get_source_videos_from_source_info_dict(source_info_dict=source_info_dict)
    return SourceCreate(
        created_by=user_id,
        **handler.map_source_info_dict_to_source_dict(
            source_info_dict=source_info_dict, source_videos=source_videos
        ),
    )


async def get_source_videos_from_source_info_dict(
    source_info_dict: dict[str, Any]
) -> list[VideoCreate]:
    """
    Get a list of `Video` objects from a source_info_dict.

    Parameters:
        source_info_dict (dict): The source_info_dict.

    Returns:
        list: The list of `Video` objects.
    """
    handler = get_handler_from_url(url=source_info_dict["metadata"]["url"])
    entries = source_info_dict["entries"]
    playlists = entries if entries[0].get("entries") else [source_info_dict]
    video_dicts = [
        handler.map_source_info_dict_entity_to_video_dict(
            source_id=source_info_dict["source_id"], entry_info_dict=entry_info_dict
        )
        for playlist in playlists
        for entry_info_dict in playlist.get("entries", [])
    ]
    videos = [VideoCreate(**video_dict) for video_dict in video_dicts]
    return videos


async def refresh_all_sources(db: Session) -> list[Source]:
    """
    Fetches new data from yt-dlp for all Sources.

    Args:
        db (Session): The database session.

    Returns:
        The list of refreshed Sources.
    """
    sources = await crud.source.get_all(db=db) or []
    return await refresh_sources(sources=sources, db=db)


async def refresh_sources(sources: list[Source], db: Session) -> list[Source]:
    """
    Fetches new data from yt-dlp for each Source.

    Args:
        sources: The list of sources to refresh.
        db (Session): The database session.

    Returns:
        The list of refreshed Sources.
    """
    return [await crud.source.fetch_source(source_id=source.id, db=db) for source in sources]


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
            await crud.video.create(in_obj=new_video, db=db)

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
