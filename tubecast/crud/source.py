from sqlmodel import Session

from tubecast import models

from .base import BaseCRUD


class SourceCRUD(BaseCRUD[models.Source, models.SourceCreate, models.SourceUpdate]):
    async def create_with_owner_id(
        self, db: Session, *, obj_in: models.SourceCreate, owner_id: str
    ) -> models.Source:
        """
        Create a new source with an owner_id.

        Args:
            db (Session): The database session.
            obj_in (models.SourceCreate): The source to create.
            owner_id (str): The owner_id to set on the source.

        Returns:
            models.Source: The created source.
        """
        obj_in.owner_id = owner_id
        return await self.create(db, obj_in=obj_in)

    async def get_multi_by_owner_id(
        self, db: Session, *, owner_id: str, skip: int = 0, limit: int = 100
    ) -> list[models.Source]:
        """
        Retrieve multiple sources by owner_id.

        Args:
            db (Session): The database session.
            owner_id (str): The owner_id to filter by.
            skip (int): The number of rows to skip. Defaults to 0.
            limit (int): The maximum number of rows to return. Defaults to 100.

        Returns:
            list[models.Source]: A list of sources that match the given criteria.
        """
        return await self.get_multi(db=db, owner_id=owner_id, skip=skip, limit=limit)


source = SourceCRUD(models.Source)
