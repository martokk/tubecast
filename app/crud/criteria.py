from typing import Any

from sqlalchemy.sql.elements import BinaryExpression
from sqlmodel import Session

from app import models
from app.models.criteria import CriteriaField

from .base import BaseCRUD


class CriteriaCRUD(BaseCRUD[models.Criteria, models.CriteriaCreate, models.CriteriaUpdate]):
    async def create(
        self, db: Session, *, obj_in: models.CriteriaCreate, **kwargs: Any
    ) -> models.Criteria:
        """
        Create a new record.

        Args:
            db (Session): The database session.
            obj_in: The object to create.

        Returns:
            The created object.

        Raises:
            ValueError: If the value is not an integer.
        """

        # Validate the value
        if obj_in.field in [
            CriteriaField.RELEASED.value,
            CriteriaField.CREATED.value,
            CriteriaField.DURATION.value,
        ]:
            try:
                int(obj_in.value)
            except ValueError:
                raise ValueError("Value must be an integer")

        return await super().create(db, obj_in=obj_in, **kwargs)

    async def update(
        self,
        db: Session,
        *args: BinaryExpression[Any],
        obj_in: models.CriteriaUpdate,
        exclude_none: bool = True,
        exclude_unset: bool = True,
        **kwargs: Any,
    ) -> models.Criteria:
        """
        Update an existing record.

        Args:
            obj_in (models.CriteriaCreate): The updated object.
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

        # Validate the value
        if obj_in.field in [
            CriteriaField.RELEASED.value,
            CriteriaField.CREATED.value,
            CriteriaField.DURATION.value,
        ]:
            try:
                int(obj_in.value)
            except ValueError:
                raise ValueError("Value must be an integer")

        return await super().update(
            db,
            *args,
            obj_in=obj_in,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
            **kwargs,
        )


criteria = CriteriaCRUD(models.Criteria)
