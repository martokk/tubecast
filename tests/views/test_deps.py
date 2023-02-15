from sqlmodel import Session

from app import models
from app.views import deps


async def test_get_db() -> None:
    """
    Test get_db() dependency.
    """
    db = next(deps.get_db())
    assert isinstance(db, Session)
