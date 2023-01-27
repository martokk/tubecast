from typing import Any, Generic, Type, TypeVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import BinaryExpression
from sqlmodel import Session, SQLModel, select

from tubecast.crud import DeleteError, RecordAlreadyExistsError, RecordNotFoundError

ModelType = TypeVar("ModelType", bound=SQLModel)
ModelCreateType = TypeVar("ModelCreateType", bound=SQLModel)
ModelUpdateType = TypeVar("ModelUpdateType", bound=SQLModel)


class BaseCRUD(Generic[ModelType, ModelCreateType, ModelUpdateType]):
    def __init__(self, model: type[ModelType]) -> None:
        """
        Initialize the CRUD object.

        Args:
            model: The model class to operate on.
        """
        self.model = model

    async def get_all(self, db: Session) -> list[ModelType]:
        """
        Get all records for the model.

        Args:
            db (Session): The database session.

        Returns:
            A list of all records, or None if there are none.
        """
        statement = select(self.model)
        return db.exec(statement).all() or []

    async def get(self, *args: BinaryExpression[Any], db: Session, **kwargs: Any) -> ModelType:
        """
        Get a record by its primary key(s).

        Args:
            db (Session): The database session.
            args: Binary expressions to filter by.
            kwargs: Keyword arguments to filter by.

        Returns:
            The matching record.

        Raises:
            RecordNotFoundError: If no matching record is found.
        """
        statement = select(self.model).filter(*args).filter_by(**kwargs)

        result = db.exec(statement).first()
        if result is None:
            raise RecordNotFoundError(
                f"{self.model.__name__}({args=} {kwargs=}) not found in database"
            )
        return result

    async def get_or_none(
        self, db: Session, *args: BinaryExpression[Any], **kwargs: Any
    ) -> ModelType | None:
        """
        Get a record by its primary key(s), or return None if no matching record is found.

        Args:
            db (Session): The database session.
            args: Binary expressions to filter by.
            kwargs: Keyword arguments to filter by.

        Returns:
            The matching record, or None.
        """
        try:
            result = await self.get(db=db, *args, **kwargs)
        except RecordNotFoundError:
            return None
        return result

    async def get_multi(
        self,
        *args: BinaryExpression[Any],
        db: Session,
        skip: int = 0,
        limit: int = 100,
        **kwargs: Any,
    ) -> list[ModelType]:
        """
        Retrieve multiple rows from the database that match the given criteria.

        Args:
            db (Session): The database session.
            skip: The number of rows to skip.
            limit: The maximum number of rows to return.
            args: Binary expressions used to filter the rows to be retrieved.
            kwargs: Keyword arguments used to filter the rows to be retrieved.

        Returns:
            A list of records that match the given criteria.
        """

        statement = select(self.model).filter(*args).filter_by(**kwargs).offset(skip).limit(limit)
        return db.exec(statement).fetchmany()

    async def create(self, db: Session, *, in_obj: ModelCreateType) -> ModelType:
        """
        Create a new record.

        Args:
            db (Session): The database session.
            in_obj: The object to create.

        Returns:
            The created object.

        Raises:
            RecordAlreadyExistsError: If the record already exists.
        """
        out_obj = self.model(**in_obj.dict())

        db.add(out_obj)
        try:
            db.commit()
        except IntegrityError as exc:
            raise RecordAlreadyExistsError(
                f"{self.model.__name__}({in_obj=}) already exists in database"
            ) from exc
        db.refresh(out_obj)
        return out_obj

    async def update(
        self,
        db: Session,
        *args: BinaryExpression[Any],
        in_obj: ModelUpdateType,
        exclude_none=True,
        exclude_unset=True,
        **kwargs: Any,
    ) -> ModelType:
        """
        Update an existing record.

        Args:
            in_obj: The updated object.
            args: Binary expressions to filter by.
            db (Session): The database session.
            exclude_none: Whether to exclude None values from the update.
            exclude_unset: Whether to exclude unset values from the update.
            kwargs: Keyword arguments to filter by.

        Returns:
            The updated object.

        Raises:
            ValueError: If no filters are provided.
        """
        if not args and not kwargs:
            raise ValueError("crud.base.update() Must provide at least one filter")
        db_obj = await self.get(db=db, *args, **kwargs)

        in_obj_values = in_obj.dict(exclude_unset=exclude_unset, exclude_none=exclude_none)
        db_obj_values = db_obj.dict()
        for in_obj_key, in_obj_value in in_obj_values.items():
            if in_obj_value != db_obj_values[in_obj_key]:
                setattr(db_obj, in_obj_key, in_obj_value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    async def remove(self, *args: BinaryExpression[Any], db: Session, **kwargs: Any) -> None:
        """
        Delete a record.

        Args:
            db (Session): The database session.
            args: Binary expressions to filter by.
            kwargs: Keyword arguments to filter by.

        Raises:
            DeleteError: If an error occurs while deleting the record.
        """
        db_obj = await self.get(db=db, *args, **kwargs)
        try:
            db.delete(db_obj)
            db.commit()
        except Exception as exc:
            raise DeleteError("Error while deleting") from exc
