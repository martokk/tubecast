from urllib.parse import ParseResult, urlparse

from app.handlers.exceptions import HandlerNotFoundError

from .base import ServiceHandler
from .rumble import RumbleHandler
from .tubesubs import TubeSubsHandler
from .youtube import YoutubeHandler

registered_handlers = [YoutubeHandler(), RumbleHandler(), TubeSubsHandler()]


def get_handler_from_url(url: str | ParseResult) -> ServiceHandler:
    url = url if isinstance(url, ParseResult) else urlparse(url=url)
    subdomain = url.netloc.split(":")[0]
    domain_name = ".".join(subdomain.split(".")[-2:])

    if domain_name in YoutubeHandler.DOMAINS or subdomain in YoutubeHandler.DOMAINS:
        return YoutubeHandler()
    if domain_name in RumbleHandler.DOMAINS or subdomain in RumbleHandler.DOMAINS:
        return RumbleHandler()
    if domain_name in TubeSubsHandler.DOMAINS or subdomain in TubeSubsHandler.DOMAINS:
        return TubeSubsHandler()
    raise HandlerNotFoundError(f"A handler could not be found for url: `{str(url)}`.")


def get_handler_from_string(handler_string: str) -> ServiceHandler:
    if handler_string == "YoutubeHandler" or handler_string == "Youtube":
        return YoutubeHandler()
    if handler_string == "RumbleHandler" or handler_string == "Rumble":
        return RumbleHandler()
    if handler_string == "TubeSubsHandler" or handler_string == "TubeSubs":
        return TubeSubsHandler()
    raise HandlerNotFoundError(f"A handler could not be found for {handler_string=}.")
