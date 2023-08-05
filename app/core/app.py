import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_utils.tasks import repeat_every
from sqlmodel import Session

from app import crud, logger, settings
from app.api import deps
from app.api.v1.api import api_router
from app.core import notify
from app.db.backup import backup_database
from app.db.init_db import init_initial_data
from app.paths import FEEDS_PATH, STATIC_PATH
from app.services.fetch import fetch_all_sources
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
    # Get time
    utcnow = datetime.datetime.utcnow()
    central_time_diff = datetime.timedelta(hours=-5)
    central_time = utcnow + central_time_diff
    current_time = central_time.time()

    # Define the start and end times for the night
    start_night = datetime.time(22, 0)  # 10 PM
    start_morning = datetime.time(7, 0)  # 7 AM

    # Check if the current time is between night_start and night_end
    if start_night <= current_time or current_time < start_morning:
        print("Current Time (UTC-5) is:", current_time)
        print(f"repeating_fetch_all_sources() is paused from {start_night} to {start_morning}.")
    else:
        if (
            (datetime.time(8, 0) <= current_time and current_time <= datetime.time(9, 0))
            or (datetime.time(10, 0) <= current_time and current_time <= datetime.time(12, 0))
            or (datetime.time(13, 0) <= current_time and current_time <= datetime.time(14, 0))
            or (datetime.time(15, 0) <= current_time and current_time <= datetime.time(16, 0))
        ):
            print("Current Time (UTC-5) is:", current_time)
            print("repeating_fetch_all_sources() is paused from 8-9am, 10-12pm, 1-2pm, 3-4pm")

        logger.debug("Repeating fetch of All Sources...")
        db: Session = next(deps.get_db())
        fetch_results = await fetch_all_sources(db=db)
        logger.success(f"Completed refreshing {fetch_results.sources} Sources from yt-dlp.")


# @app.on_event("startup")  # type: ignore
# @repeat_every(seconds=settings.REFRESH_VIDEOS_INTERVAL_MINUTES * 60, wait_first=True)
# async def repeating_refresh_videos() -> None:  # pragma: no cover
#     """
#     Refreshes all Videos that meet criteria with updated data from yt-dlp.
#     """
#     logger.debug("Repeating refresh of Videos...")
#     db: Session = next(deps.get_db())
#     refreshed_videos = await refresh_all_videos(db=db)
#     logger.success(f"Completed refreshing {len(refreshed_videos)} Videos from yt-dlp.")


@app.on_event("startup")  # type: ignore
@repeat_every(seconds=60 * 60 * 12, wait_first=True)  # 12 hours
async def repeating_backup_db() -> None:  # pragma: no cover
    """
    Refreshes all Videos that meet criteria with updated data from yt-dlp.
    """
    db: Session = next(deps.get_db())
    await backup_database(db=db)


# @app.on_event("startup")  # type: ignore
# async def on_startup_export(db: Session = next(deps.get_db())) -> None:
#     """
#     On startup, export all Sources to a YAML file.

#     Args:
#         db (Session): Database session.
#     """
#     await export_sources(db=db)


# @app.on_event("startup")  # type: ignore
# async def on_startup_import(db: Session = next(deps.get_db())) -> None:
#     """
#     On startup, import all Sources from a YAML file.

#     Args:
#         db (Session): Database session.
#     """
#     await import_sources(db=db)


# @app.on_event("startup")  # type: ignore
# async def on_startup_temp(db: Session = next(deps.get_db())) -> None:
#     """
#     TODO: DELETE THIS FUNCTION
#     """
#     user: models.User = await crud.user.get(db=db, username="martokk")

#     sources = await crud.source.get_all(db=db)

#     for source in sources:
#         await crud.source.add_default_filters(db=db, source=source, user_id=user.id)
