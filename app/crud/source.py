from typing import Any

from loguru import logger as _logger
from sqlalchemy.sql.elements import BinaryExpression
from sqlmodel import Session

from app import crud, handlers, models
from app.crud.base import BaseCRUD
from app.models.criteria import CriteriaField, CriteriaOperator, CriteriaUnitOfMeasure
from app.models.source_video_link import SourceOrderBy
from app.services.feed import delete_rss_file
from app.services.source import get_source_from_source_info_dict, get_source_info_dict

logger = _logger.bind(name="logger")


class SourceCRUD(BaseCRUD[models.Source, models.SourceCreate, models.SourceUpdate]):
    async def update(
        self,
        db: Session,
        *args: BinaryExpression[Any],
        obj_in: models.SourceUpdate,
        exclude_none: bool = True,
        exclude_unset: bool = True,
        **kwargs: Any,
    ) -> models.Source:
        """
        Update an existing record.

        Args:
            obj_in (ModelUpdateType): The updated object.
            args (BinaryExpression): Binary expressions to filter by.
            db (Session): The database session.
            exclude_none (bool): Whether to exclude None values from the update.
            exclude_unset (bool): Whether to exclude unset values from the update.
            kwargs (Any): Keyword arguments to filter by.

        Returns:
            The updated object.

        Raises:
            ValueError: If no filters are provided.
        """

        # If reverse_import_order, delete all existing videos
        if obj_in.reverse_import_order:
            await self.delete_all_videos(db=db, source_id=kwargs["id"])

        return await super().update(
            db,
            *args,
            obj_in=obj_in,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
            **kwargs,
        )

    async def remove(self, db: Session, *args: BinaryExpression[Any], **kwargs: Any) -> None:
        if source_id := kwargs.get("id"):

            #

            # Delete RSS file
            try:
                await delete_rss_file(id=source_id)
            except FileNotFoundError as e:
                logger.error(e)

            # Delete source
            return await super().remove(db, *args, **kwargs)
        raise ValueError("No source id provided")

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
        handler = handlers.get_handler_from_url(url=url)
        url = handler.sanitize_source_url(url=url)
        source_id = await models.source.generate_source_id_from_url(url=url)

        # Check if the source already exists
        db_source = await self.get_or_none(id=source_id, db=db)
        if not db_source:
            # Fetch source information from yt-dlp and create the source object
            source_info_dict = await get_source_info_dict(
                source_id=source_id, url=url, playlistend=100, dateafter="now-20y"
            )

            _source = await get_source_from_source_info_dict(
                source_info_dict=source_info_dict, created_by_user_id=user_id
            )

            # Save the source to the database
            db_source = await self.create(obj_in=_source, db=db)
            logger.success(f"Created source {_source.id} from url {url}")

        # Add the Source to the user's Sources
        await crud.user.add_source(db=db, user_id=user_id, source=db_source)

        # Create default filters ("shorts", "regular", "podcasts")
        await self.add_default_filters(db=db, source=db_source, user_id=user_id)

        return db_source

    async def add_default_filters(self, db: Session, source: models.Source, user_id: str) -> None:
        """
        Add default filters to a source.

        Args:
            db (Session): The database session.
            source (models.Source): The source to add the default filters to.
        """

        # Filter: Shorts
        filter_shorts = await crud.filter.create(
            db=db,
            obj_in=models.FilterCreate(
                name="Shorts",
                source_id=source.id,
                ordered_by=SourceOrderBy.RELEASED_AT.value,
                created_by=user_id,
            ),
        )
        await crud.criteria.create(
            db=db,
            obj_in=models.CriteriaCreate(
                filter_id=filter_shorts.id,
                field=CriteriaField.DURATION.value,
                operator=CriteriaOperator.SHORTER_THAN.value,
                value="90",
                unit_of_measure=CriteriaUnitOfMeasure.SECONDS.value,
            ),
        )

        # Filter: Regular Videos
        filter_regular = await crud.filter.create(
            db=db,
            obj_in=models.FilterCreate(
                name="Regular Videos",
                source_id=source.id,
                ordered_by=SourceOrderBy.RELEASED_AT.value,
                created_by=user_id,
            ),
        )
        await crud.criteria.create(
            db=db,
            obj_in=models.CriteriaCreate(
                filter_id=filter_regular.id,
                field=CriteriaField.DURATION.value,
                operator=CriteriaOperator.LONGER_THAN.value,
                value="90",
                unit_of_measure=CriteriaUnitOfMeasure.SECONDS.value,
            ),
        )
        await crud.criteria.create(
            db=db,
            obj_in=models.CriteriaCreate(
                filter_id=filter_regular.id,
                field=CriteriaField.DURATION.value,
                operator=CriteriaOperator.SHORTER_THAN.value,
                value="35",
                unit_of_measure=CriteriaUnitOfMeasure.MINUTES.value,
            ),
        )

        # Filter: Podcasts
        filter_podcasts = await crud.filter.create(
            db=db,
            obj_in=models.FilterCreate(
                name="Podcasts",
                source_id=source.id,
                ordered_by=SourceOrderBy.RELEASED_AT.value,
                created_by=user_id,
            ),
        )
        await crud.criteria.create(
            db=db,
            obj_in=models.CriteriaCreate(
                filter_id=filter_podcasts.id,
                field=CriteriaField.DURATION.value,
                operator=CriteriaOperator.LONGER_THAN.value,
                value="35",
                unit_of_measure=CriteriaUnitOfMeasure.MINUTES.value,
            ),
        )

    async def delete_all_videos(self, db: Session, source_id: str) -> None:
        """
        Delete all videos from a source.

        Args:
            db (Session): The database session.
            source_id (str): The source id.
        """
        source = await self.get(db=db, id=source_id)
        for video in source.videos:
            await crud.video.remove(db=db, id=video.id)


source = SourceCRUD(models.Source)
