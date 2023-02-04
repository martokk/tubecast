from sqlmodel import Session

from tubecast import models
from tubecast.views import deps


async def test_get_db() -> None:
    """
    Test get_db() dependency.
    """
    db = next(deps.get_db())
    assert isinstance(db, Session)
