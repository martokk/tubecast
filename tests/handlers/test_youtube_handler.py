import pytest
from fastapi.testclient import TestClient

from tubecast import settings
from tubecast.handlers.youtube import YoutubeHandler

HANDLER = YoutubeHandler()


def test_force_watch_v_format() -> None:
    """
    Test that the force_watch_v_format method returns the correct URL.
    """
    # Test regular watch URL
    watch_url = "https://www.youtube.com/watch?v=VIDEO_ID"
    assert HANDLER.force_watch_v_format(url=watch_url) == watch_url

    # Test short URL
    url2 = "https://www.youtube.com/shorts/VIDEO_ID"
    assert HANDLER.force_watch_v_format(url=url2) == watch_url

    # Test invalid URL
    url3 = "https://www.youtube.com/invalid/VIDEO_ID"
    with pytest.raises(ValueError):
        HANDLER.force_watch_v_format(url=url3)
