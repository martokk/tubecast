from importlib import metadata as importlib_metadata
from os import getenv as _getenv

from dotenv import load_dotenv as _load_dotenv
from loguru import logger as _logger

from app.models.settings import Settings as _Settings
from app.paths import ENV_FILE as _ENV_FILE
from app.paths import ERROR_LOG_FILE as _ERROR_LOG_FILE
from app.paths import FETCH_LOG_FILE as _FETCH_LOG_FILE
from app.paths import LOG_FILE as _LOG_FILE
from app.paths import YTDLP_LOG_FILE as _YTDLP_LOG_FILE


def get_version() -> str:
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


# Load ENV_FILE from ENV, else from app.paths
_env_file = _getenv("ENV_FILE", _ENV_FILE)
_load_dotenv(dotenv_path=_env_file)

# Load settings
version: str = get_version()
settings = _Settings(VERSION=version)  # type: ignore

# Setup Loggers
_logger.add(
    _LOG_FILE,
    filter=lambda record: record["extra"].get("name") == "logger",
    level=settings.LOG_LEVEL,
    rotation="10 MB",
)
_logger.add(
    _ERROR_LOG_FILE,
    filter=lambda record: record["extra"].get("name") == "logger",
    level="ERROR",
    rotation="10 MB",
)
_logger.add(
    _FETCH_LOG_FILE,
    filter=lambda record: record["extra"].get("name") == "fetch_logger",
    level="ERROR",
    rotation="10 MB",
)
_logger.add(
    _YTDLP_LOG_FILE,
    filter=lambda record: record["extra"].get("name") == "ytdlp_logger",
    level=settings.LOG_LEVEL,
    rotation="10 MB",
)

# Expose main logger
logger = _logger.bind(name="logger")
