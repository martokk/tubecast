import pytest

from app.handlers import get_handler_from_string, get_handler_from_url
from app.handlers.exceptions import HandlerNotFoundError


def test_get_handler_from_url() -> None:
    """
    Tests the `get_handler_from_url` function.
    """
    url = "https://www.youtube.com/watch?v=1234567890"
    handler = get_handler_from_url(url=url)
    assert handler.__class__.__name__ == "YoutubeHandler"

    url = "https://www.rumble.com/v1234567890"
    handler = get_handler_from_url(url=url)
    assert handler.__class__.__name__ == "RumbleHandler"

    url = "https://www.bitchute.com/video/1234567890"
    with pytest.raises(HandlerNotFoundError):
        get_handler_from_url(url=url)


def test_get_handler_from_string() -> None:
    """
    Tests the `get_handler_from_string` function.
    """
    handler_string = "YoutubeHandler"
    handler = get_handler_from_string(handler_string=handler_string)
    assert handler.__class__.__name__ == "YoutubeHandler"

    handler_string = "RumbleHandler"
    handler = get_handler_from_string(handler_string=handler_string)
    assert handler.__class__.__name__ == "RumbleHandler"

    handler_string = "BitchuteHandler"
    with pytest.raises(HandlerNotFoundError):
        get_handler_from_string(handler_string=handler_string)
