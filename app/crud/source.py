from typing import Any

from sqlalchemy.sql.elements import BinaryExpression
from sqlmodel import Session

from app import crud, fetch_logger, handlers, logger, models, settings
from app.crud.base import BaseCRUD
from app.models.source import generate_source_id_from_url
from app.services.feed import build_rss_file, delete_rss_file
from app.services.source import (
    add_new_source_videos_from_fetched_videos,
    get_source_from_source_info_dict,
    get_source_info_dict,
    get_source_videos_from_source_info_dict,
)
from app.services.video import get_videos_needing_refresh, refresh_videos


class SourceCRUD(BaseCRUD[models.Source, models.SourceCreate, models.SourceUpdate]):
    async def remove(self, db: Session, *args: BinaryExpression[Any], **kwargs: Any) -> None:
        if source_id := kwargs.get("id"):
            try:
                await delete_rss_file(source_id=source_id)
            except FileNotFoundError as e:
                logger.error(e)
        return await super().remove(db, *args, **kwargs)

    async def create_source_from_url(self, db: Session, url: str, user_id: str) -> models.Source:
        """
        Create a new source from a URL.

        Args:
            url: The URL to create the source from.
            user_id(str): The user id
            db (Session): The database session.

        Returns:
            The created source.

        Raises:
            RecordAlreadyExistsError: If a source already exists for the given URL.
        """
        source_id = await generate_source_id_from_url(url=url)

        # Check if the source already exists
        db_source = await self.get_or_none(id=source_id, db=db)
        if db_source:
            raise crud.RecordAlreadyExistsError("Record already exists for url.")

        # Fetch source information from yt-dlp and create the source object
        source_info_dict = await get_source_info_dict(
            source_id=source_id,
            url=url,
            extract_flat=True,
            playlistreverse=True,
            playlistend=settings.BUILD_FEED_RECENT_VIDEOS,
            dateafter=settings.BUILD_FEED_DATEAFTER,
        )
        _source = await get_source_from_source_info_dict(
            source_info_dict=source_info_dict, user_id=user_id
        )

        # Save the source to the database
        db_source = await self.create(obj_in=_source, db=db)
        logger.success(f"Created source {_source.id} from url {url}")
        return db_source

    # async def create_with_owner_id(
    #     self, db: Session, *, obj_in: models.SourceCreate, owner_id: str
    # ) -> models.Source:
    #     """
    #     Create a new source with an owner_id.

    #     Args:
    #         db (Session): The database session.
    #         obj_in (models.SourceCreate): The source to create.
    #         owner_id (str): The owner_id to set on the source.

    #     Returns:
    #         models.Source: The created source.
    #     """
    #     obj_in.owner_id = owner_id
    #     return await self.create(db, obj_in=obj_in)

    async def fetch_source(self, db: Session, id: str) -> models.FetchResults:
        """
        Fetch new data from yt-dlp for the source and update the source in the database.

        This function will also delete any videos that are no longer associated with the source.

        Args:
            id: The id of the source to fetch and update.
            db (Session): The database session.

        Returns:
            models.FetchResult: The result of the fetch.
        """

        db_source = await self.get(id=id, db=db)
        logger.debug(f"Fetching Source(id='{db_source.id}, name='{db_source.name}')")
        fetch_logger.debug(f"Fetching Source(id='{db_source.id}, name='{db_source.name}')")

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
        db_source = await self.update(obj_in=models.SourceUpdate(**_source.dict()), id=id, db=db)

        # Use the source information to fetch the videos
        fetched_videos = await get_source_videos_from_source_info_dict(
            source_info_dict=source_info_dict
        )

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
        videos_needing_refresh = await get_videos_needing_refresh(
            videos=db_source.videos, older_than_hours=handler.MAX_VIDEO_AGE_HOURS
        )
        refreshed_videos = await refresh_videos(
            videos_needing_refresh=videos_needing_refresh,
            db=db,
        )

        # Build RSS File
        await build_rss_file(source=db_source)

        logger.success(
            f"Completed fetching Source(id='{db_source.id}'). "
            f"[{len(new_videos)}/{len(deleted_videos)}/{len(refreshed_videos)}] "
            f"Added {len(new_videos)} new videos. "
            f"Deleted {len(deleted_videos)} orphaned videos. "
            f"Refreshed {len(refreshed_videos)} videos."
        )
        fetch_logger.success(
            f"Completed fetching Source(id='{db_source.id}'). "
            f"[{len(new_videos)}/{len(deleted_videos)}/{len(refreshed_videos)}] "
            f"Added {len(new_videos)} new videos. "
            f"Deleted {len(deleted_videos)} orphaned videos. "
            f"Refreshed {len(refreshed_videos)} videos."
        )

        return models.FetchResults(
            sources=1,
            added_videos=len(new_videos),
            deleted_videos=len(deleted_videos),
            refreshed_videos=len(refreshed_videos),
        )

    async def fetch_all_sources(self, db: Session) -> models.FetchResults:
        """
        Fetch all sources.

        Args:
            db (Session): The database session.

        Returns:
            models.FetchResults: The results of the fetch.
        """
        logger.debug("Fetching ALL Sources...")
        fetch_logger.debug("Fetching ALL Sources...")
        sources = await self.get_all(db=db) or []
        results = models.FetchResults()

        for _source in sources:
            source_fetch_results = await self.fetch_source(id=_source.id, db=db)
            results += source_fetch_results

        logger.success(
            f"Completed fetching All ({results.sources}) Sources. "
            f"[{results.added_videos}/{results.deleted_videos}/{results.refreshed_videos}]"
            f"Added {results.added_videos} new videos. "
            f"Deleted {results.deleted_videos} orphaned videos. "
            f"Refreshed {results.refreshed_videos} videos."
        )
        fetch_logger.success(
            f"Completed fetching All ({results.sources}) Sources. "
            f"[{results.added_videos}/{results.deleted_videos}/{results.refreshed_videos}]"
            f"Added {results.added_videos} new videos. "
            f"Deleted {results.deleted_videos} orphaned videos. "
            f"Refreshed {results.refreshed_videos} videos."
        )
        return results


source = SourceCRUD(models.Source)
