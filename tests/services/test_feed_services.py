import datetime

import pytest

from app.services.feed import SourceFeedGenerator, get_published_at


def test_missing_feed_or_source() -> None:
    with pytest.raises(ValueError):
        SourceFeedGenerator(filter=None, source=None)


def test_get_published_date() -> None:
    """
    Tests the `get_published_date` function.
    """
    created_at = datetime.datetime(2021, 1, 1, 0, 0, 0)
    released_at = datetime.datetime(2021, 1, 1, 0, 0, 0)
    assert get_published_at(created_at=created_at, released_at=released_at) == created_at

    created_at = datetime.datetime(2021, 1, 1, 0, 0, 0)
    released_at = datetime.datetime(2021, 1, 1, 0, 0, 1)
    assert get_published_at(created_at=created_at, released_at=released_at) == released_at

    created_at = datetime.datetime(2021, 1, 1, 0, 0, 0)
    released_at = datetime.datetime(2021, 1, 2, 0, 0, 0)
    assert get_published_at(created_at=created_at, released_at=released_at) == released_at

    created_at = datetime.datetime(2021, 1, 1, 0, 0, 0)
    released_at = datetime.datetime(2021, 1, 2, 0, 0, 1)
    assert get_published_at(created_at=created_at, released_at=released_at) == released_at

    created_at = datetime.datetime(2021, 1, 1, 0, 0, 0)
    assert get_published_at(created_at=created_at, released_at=None) == created_at

    created_at = datetime.datetime(2021, 1, 1, 0, 0, 1)
    assert get_published_at(created_at=created_at, released_at=None) == created_at

    created_at = datetime.datetime(2021, 1, 1, 0, 0, 0)
    released_at = datetime.datetime(2021, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    assert get_published_at(created_at=created_at, released_at=released_at) == created_at
