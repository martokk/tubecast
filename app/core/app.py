from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_utils.tasks import repeat_every
from sqlmodel import Session

from app import crud, logger, settings, version
from app.api import deps
from app.api.v1.api import api_router
from app.core import notify
from app.db.init_db import init_initial_data
from app.paths import FEEDS_PATH, STATIC_PATH
from app.services.source import fetch_all_sources
from app.services.video import refresh_all_videos
from app.views.router import views_router

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    debug=settings.DEBUG,
)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(views_router)

FEEDS_PATH.mkdir(parents=True, exist_ok=True)
app.mount("/feed", StaticFiles(directory=FEEDS_PATH), name="feed")

# STATIC_PATH.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_PATH))


@app.on_event("startup")  # type: ignore
async def on_startup(db: Session = next(deps.get_db())) -> None:
    """
    Event handler that gets called when the application starts.
    Logs application start and creates database and tables if they do not exist.

    Args:
        db (Session): Database session.
    """
    logger.info("--- Start FastAPI ---")
    logger.debug("Starting FastAPI App...")
    if settings.NOTIFY_ON_START:
        total_users = await crud.user.count(db=db)
        total_sources = await crud.source.count(db=db)
        total_videos = await crud.video.count(db=db)

        await notify.notify(
            text=(
                f"{settings.PROJECT_NAME}('{settings.ENV_NAME}') started.\n\n"
                f"Total Users: {total_users}\n"
                f"Total Sources: {total_sources}\n"
                f"Total Videos: {total_videos}\n"
            )
        )

    await init_initial_data(db=db)


@app.on_event("startup")  # type: ignore
@repeat_every(seconds=settings.REFRESH_SOURCES_INTERVAL_MINUTES * 60, wait_first=True)
async def repeating_fetch_all_sources() -> None:  # pragma: no cover
    """
    Fetches all Sources from yt-dlp.
    """
    logger.debug("Repeating fetch of All Sources...")
    db: Session = next(deps.get_db())
    fetch_results = await fetch_all_sources(db=db)
    logger.success(f"Completed refreshing {fetch_results.sources} Sources from yt-dlp.")


@app.on_event("startup")  # type: ignore
@repeat_every(seconds=settings.REFRESH_VIDEOS_INTERVAL_MINUTES * 60, wait_first=True)
async def repeating_refresh_videos() -> None:  # pragma: no cover
    """
    Refreshes all Videos that meet criteria with updated data from yt-dlp.
    """
    logger.debug("Repeating refresh of Videos...")
    db: Session = next(deps.get_db())
    refreshed_videos = await refresh_all_videos(db=db)
    logger.success(f"Completed refreshing {len(refreshed_videos)} Videos from yt-dlp.")
