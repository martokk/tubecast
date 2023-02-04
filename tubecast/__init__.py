from importlib import metadata as importlib_metadata
from os import getenv as _getenv

from dotenv import load_dotenv as _load_dotenv
from loguru import logger as _logger

from python_fastapi_stack.models.settings import Settings as _Settings
from python_fastapi_stack.paths import ENV_FILE as _ENV_FILE
from python_fastapi_stack.paths import LOG_FILE as _LOG_FILE


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

# Configure logger
_logger.add(_LOG_FILE, level=settings.LOG_LEVEL, rotation="10 MB")
_logger.info(f"Log level set by .env to '{settings.LOG_LEVEL}'")
logger = _logger
