import shutil
from datetime import datetime
from pathlib import Path

from sqlmodel import Session

from app import crud, logger, paths


async def backup_database(db: Session) -> Path:
    """
    Backs up the database.

    Args:
        db (Session): The database session.

    Returns:
        Path: The path to the backup file.
    """
    logger.debug("Backing up database...")

    dt_str = datetime.now().strftime("%m-%d-%y - %H-%M-%S")
    total_sources = await crud.source.count(db=db)
    filename = f"database - {dt_str} - {total_sources}.sqlite3"

    db_backup_file = paths.DB_BACKUP_PATH / filename
    shutil.copy(src=paths.DATABASE_FILE, dst=db_backup_file)

    if not db_backup_file.exists():
        raise FileNotFoundError(f"Database backup file not found: {db_backup_file}")
    return db_backup_file
