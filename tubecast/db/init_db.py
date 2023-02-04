from typing import Any

from sqlalchemy.engine.base import Engine
from sqlmodel import Session, SQLModel

from python_fastapi_stack import crud, logger, models, settings
from python_fastapi_stack.db.session import engine as _engine


async def create_all(engine: Engine = _engine, sqlmodel_create_all: bool = False) -> None:
    """
    Create all tables in the database.

    Args:
        engine (Engine): database engine.
        sqlmodel_create_all (bool): whether to create all tables using SQLModel.

    Returns:
        None
    """
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line or use
    # sqlmodel_create_all=True
    if sqlmodel_create_all:
        logger.debug("Initializing database...")
        SQLModel.metadata.create_all(bind=engine)
    return


async def init_initial_data(db: Session, **kwargs: Any) -> None:
    await create_all(**kwargs)

    user = await crud.user.get_or_none(db=db, username=settings.FIRST_SUPERUSER_USERNAME)
    if not user:
        user_create = models.UserCreateWithPassword(
            username=settings.FIRST_SUPERUSER_USERNAME,
            email=settings.FIRST_SUPERUSER_EMAIL,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        await crud.user.create_with_password(db=db, obj_in=user_create)
