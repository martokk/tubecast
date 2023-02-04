from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine

from python_fastapi_stack import paths, settings

db_url = f"sqlite:///{paths.DATABASE_FILE}"
engine = create_engine(
    db_url,
    echo=settings.DATABASE_ECHO,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)
