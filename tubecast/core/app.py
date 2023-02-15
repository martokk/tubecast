from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_utils.tasks import repeat_every
from sqlmodel import Session

from tubecast import crud, logger, settings, version
from tubecast.api import deps
from tubecast.api.v1.api import api_router
from tubecast.core import notify
from tubecast.db.init_db import init_initial_data
from tubecast.paths import FEEDS_PATH, STATIC_PATH
from tubecast.services.video import refresh_all_videos
from tubecast.views.router import views_router

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
        await notify.notify(text=f"{settings.PROJECT_NAME}('{settings.ENV_NAME}') started.")

    await init_initial_data(db=db)


@app.on_event("startup")  # type: ignore
@repeat_every(seconds=settings.REFRESH_SOURCES_INTERVAL_MINUTES * 60, wait_first=True)
async def repeating_fetch_all_sources() -> None:  # pragma: no cover
    """
    Fetches all Sources from yt-dlp.
    """
    logger.debug("Repeating fetch of All Sources...")
    db: Session = next(deps.get_db())
    fetch_results = await crud.source.fetch_all_sources(db=db)
    logger.success(f"Completed refreshing {fetch_results.sources} Sources from yt-dlp.")


@app.on_event("startup")  # type: ignore
@repeat_every(seconds=settings.REFRESH_VIDEOS_INTERVAL_MINUTES * 60, wait_first=True)
async def repeating_refresh_videos() -> None:  # pragma: no cover
    """
    Refreshes all Videos that meet criteria with updated data from yt-dlp.
    """
    logger.debug("Repeating refresh of Videos...")
    db: Session = next(deps.get_db())
    refreshed_videos = await refresh_all_videos(
        older_than_hours=settings.MAX_VIDEO_AGE_HOURS, db=db
    )
    logger.success(f"Completed refreshing {len(refreshed_videos)} Videos from yt-dlp.")
