from sqlmodel import Session

from tubecast import models

from .base import BaseCRUD


class SourceCRUD(BaseCRUD[models.source, models.SourceCreate, models.SourceUpdate]):
    async def create_with_owner_id(
        self, db: Session, *, in_obj: models.SourceCreate, owner_id: str
    ) -> models.source:
        """
        Create a new source with an owner_id.

        Args:
            db (Session): The database session.
            in_obj (models.SourceCreate): The source to create.
            owner_id (str): The owner_id to set on the source.

        Returns:
            models.source: The created source.
        """
        in_obj.owner_id = owner_id
        return await self.create(db, in_obj=in_obj)

    async def get_multi_by_owner_id(
        self, db: Session, *, owner_id: str, skip: int = 0, limit: int = 100
    ) -> list[models.source]:
        """
        Retrieve multiple sources by owner_id.

        Args:
            db (Session): The database session.
            owner_id (str): The owner_id to filter by.
            skip (int): The number of rows to skip. Defaults to 0.
            limit (int): The maximum number of rows to return. Defaults to 100.

        Returns:
            list[models.source]: A list of sources that match the given criteria.
        """
        return await self.get_multi(db=db, owner_id=owner_id, skip=skip, limit=limit)


source = SourceCRUD(models.source)
