import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session, SQLModel

from app import paths
from app.db.backup import backup_database
from app.db.init_db import create_all


async def test_create_all(tmpdir: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test that the function creates the required tables.
    """

    # Set up test database file in a temporary directory
    db_file = Path(tmpdir.join("test_db.sqlite"))

    # Patch the database file path
    monkeypatch.setattr("app.paths.DATABASE_FILE", db_file)

    # Ensure the test database does not exist before running the function
    if os.path.exists(db_file):
        os.remove(db_file)

    # Run the function
    await create_all(sqlmodel_create_all=True)

    # Check that the required tables have been created
    tables = SQLModel.metadata.tables
    assert "source" in tables
    assert "user" in tables
    assert "fake_table" not in tables


@pytest.fixture()
def mocked_shutil_copy(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mocked_copy = MagicMock()

    def mock_copy(src: str, dst: str) -> None:
        # Instead of copying files, we'll just create empty files to simulate the copy operation
        open(dst, "w").close()
        mocked_copy(src=src, dst=dst)

    monkeypatch.setattr("shutil.copy", mock_copy)
    return mocked_copy


async def test_backup_database(db: Session, tmpdir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test that the function creates a backup of the database.
    """

    # Patch the database backup path,
    monkeypatch.setattr("app.paths.DB_BACKUP_PATH", tmpdir)

    # Call the function
    db_backup_file = await backup_database(db=db)

    # Check that the backup file exists
    assert db_backup_file.exists() is True

    # Delete the backup file
    os.remove(db_backup_file)
