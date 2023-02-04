import uvicorn

from python_fastapi_stack import logger, settings


def start_server() -> None:
    """
    Start Uvicorn server using the configuration from settings.
    """
    logger.debug("Starting uvicorn server...")
    uvicorn.run(
        settings.UVICORN_ENTRYPOINT,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.UVICORN_RELOAD,
        app_dir="",
    )
