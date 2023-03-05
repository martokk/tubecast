from typing import Any

from loguru import logger as _logger
from sqlalchemy.sql.elements import BinaryExpression
from sqlmodel import Session

from app import crud, handlers, models
from app.crud.base import BaseCRUD
from app.services.feed import delete_rss_file
from app.services.source import get_source_from_source_info_dict, get_source_info_dict

logger = _logger.bind(name="logger")


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
        handler = handlers.get_handler_from_url(url=url)
        url = handler.sanitize_source_url(url=url)
        source_id = await models.source.generate_source_id_from_url(url=url)

        # Check if the source already exists
        db_source = await self.get_or_none(id=source_id, db=db)
        if db_source:
            raise crud.RecordAlreadyExistsError("Record already exists for url.")

        # Fetch source information from yt-dlp and create the source object
        source_info_dict_kwargs = await handler.get_source_info_dict_kwargs(url=url)

        source_info_dict = await get_source_info_dict(
            source_id=source_id,
            url=url,
            **source_info_dict_kwargs,
        )

        _source = await get_source_from_source_info_dict(
            source_info_dict=source_info_dict, user_id=user_id
        )

        # Save the source to the database
        db_source = await self.create(obj_in=_source, db=db)
        logger.success(f"Created source {_source.id} from url {url}")
        return db_source


source = SourceCRUD(models.Source)
