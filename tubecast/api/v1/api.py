from fastapi import APIRouter

from tubecast import models, settings, version
from tubecast.api.v1.endpoints import feed, login, source, users, video

api_router = APIRouter()

api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/user", tags=["Users"])
api_router.include_router(video.router, prefix="/video", tags=["Videos"])
api_router.include_router(source.router, prefix="/source", tags=["Sources"])
api_router.include_router(feed.router, prefix="/feed", tags=["Feeds"])


@api_router.get("/", response_model=models.HealthCheck, tags=["status"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        dict[str, str]: Health check response.
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": "unknown",  # TODO: get version from pyproject.toml
        "description": settings.PROJECT_DESCRIPTION,
    }
