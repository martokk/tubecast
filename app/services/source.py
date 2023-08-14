from typing import Any

from sqlmodel import Session

from app import crud, paths
from app.handlers import get_handler_from_url
from app.models import Source, SourceCreate, Video, VideoCreate
from app.services.logo import create_logo_from_text, is_invalid_image
from app.services.ytdlp import get_info_dict


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
        source_id (Union[str, None]): An optional ID for the source.
        url (str | None): The URL of the Source
        extract_flat (bool | None): Whether to extract a flat list of videos in the playlist.
        playlistreverse (bool | None): Whether to reverse the playlist.
        playlistend (int | None): The index of the last video to extract.
        dateafter (str | None): The date after which to extract videos.
        reverse_import_order (bool): Whether to reverse the order of the videos in the playlist.

    Returns:
        dict: The info dictionary for the Source

    """
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
    source_info_dict: dict[str, Any],
    created_by_user_id: str,
    reverse_import_order: bool = False,
    source_name: str | None = None,
) -> SourceCreate:
    """
    Get a `Source` object from a source_info_dict.

    Parameters:
        source_info_dict (dict): The source_info_dict.
        created_by (str): user_id of authenticated user.
        reverse_import_order (bool): Whether to reverse the import order of the videos.

    Returns:
        SourceCreate: The `SourceCreate` object.
    """
    source_handler = get_handler_from_url(url=source_info_dict["metadata"]["url"])
    source_videos = get_source_videos_from_source_info_dict(source_info_dict=source_info_dict)
    handler_source_dict = source_handler.map_source_info_dict_to_source_dict(
        source_info_dict=source_info_dict, source_videos=source_videos
    )
    handler_source_dict["name"] = source_name or handler_source_dict["name"]
    return SourceCreate(
        created_by=created_by_user_id,
        reverse_import_order=reverse_import_order,
        is_deleted=False,
        is_active=True,
        **handler_source_dict,
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

    video_dicts = []
    for playlist in playlists:
        for entry_info_dict in playlist.get("entries", []):
            if (
                not entry_info_dict.get("live_status")
                or entry_info_dict.get("live_status") == "was_live"
            ):
                if (
                    "[private video]" in str(entry_info_dict.get("title")).lower()
                    or "[deleted video]" in str(entry_info_dict.get("title")).lower()
                ):
                    continue
                video_dict = handler.map_source_info_dict_entity_to_video_dict(
                    source_id=source_info_dict["source_id"], entry_info_dict=entry_info_dict
                )
                video_dicts.append(video_dict)

    return [VideoCreate(**video_dict) for video_dict in video_dicts]


async def add_new_source_info_dict_videos_to_source(
    source_info_dict: dict[str, Any], db_source: Source, db: Session
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
    fetched_videos = get_source_videos_from_source_info_dict(source_info_dict=source_info_dict)
    db_video_ids = [video.id for video in db_source.videos]

    # Add videos that were fetched, but not in the database.
    new_videos = []
    for fetched_video in fetched_videos:
        if fetched_video.id not in db_video_ids:
            new_video = VideoCreate(**fetched_video.dict())
            new_videos.append(new_video)

            db_video = await crud.video.get_or_none(db=db, id=new_video.id)
            if not db_video:
                try:
                    db_video = await crud.video.create(obj_in=new_video, db=db)
                except crud.RecordAlreadyExistsError:  # pragma: no cover
                    db_video = await crud.video.get(db=db, id=new_video.id)  # pragma: no cover

            db_source.videos.append(db_video)
            db.commit()

    return new_videos


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


async def source_needs_logo(source_logo_url: str | None) -> bool:
    """
    Checks if a logo needs to be generated.
    Will return TRUE if:
        - No logo url exists
        - URL returns a 1x1px image (ie. Rumble)

    Args:
        source_logo_url: The source logo url

    Returns:
        Boolean True/False
    """

    if not source_logo_url:
        return True

    # If is static logo url
    if "static/logos" in source_logo_url:
        return True

    if is_invalid_image(image_url=source_logo_url):
        return True

    return False


async def create_source_logo(
    source_id: str,
    source_name: str,
    background_color: str | None = None,
    border_color: str | None = None,
) -> str:
    """
    Generates a static logo from Source Name text

    Returns:
        str: logo path
    """
    logo_path = paths.LOGOS_PATH / f"{source_id}.png"
    create_logo_from_text(
        text=source_name,
        file_path=logo_path,
        background_color=background_color,
        border_color=border_color,
    )
    return f"/static/logos/{source_id}.png"
