from urllib.parse import ParseResult, urlparse

from app.handlers.exceptions import HandlerNotFoundError

from .base import ServiceHandler
from .rumble import RumbleHandler
from .youtube import YoutubeHandler

registered_handlers = [YoutubeHandler(), RumbleHandler()]


def get_handler_from_url(url: str | ParseResult) -> ServiceHandler:
    url = url if isinstance(url, ParseResult) else urlparse(url=url)
    domain_name = ".".join(url.netloc.split(".")[-2:])

    if domain_name in YoutubeHandler.DOMAINS:
        return YoutubeHandler()
    if domain_name in RumbleHandler.DOMAINS:
        return RumbleHandler()
    raise HandlerNotFoundError(f"A handler could not be found for url: `{str(url)}`.")


def get_handler_from_string(handler_string: str) -> ServiceHandler:
    if handler_string == "YoutubeHandler":
        return YoutubeHandler()
    if handler_string == "RumbleHandler":
        return RumbleHandler()
    raise HandlerNotFoundError(f"A handler could not be found for {handler_string=}.")
