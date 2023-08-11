from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse, Response
from sqlmodel import Session

from app import logger, models
from app.core.proxy import Http403ForbiddenError, reverse_proxy
from app.handlers import get_handler_from_string
from app.services.fetch import FetchCanceledError, fetch_video
from app.services.ytdlp import AwaitingTranscodingError


async def get_media_response(db: Session, video: models.Video, request: Request) -> Response:
    # Handle if the media_url is expired or missing
    handler = get_handler_from_string(handler_string=video.handler)
    refresh_interval_age_threshold = datetime.utcnow() - timedelta(
        hours=handler.REFRESH_UPDATE_INTERVAL_HOURS
    )
    if not video.media_url or video.updated_at < refresh_interval_age_threshold:
        try:
            video = await fetch_video(video_id=video.id, db=db)
        except (FetchCanceledError, AwaitingTranscodingError) as e:
            logger.error(e)
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail=f"Tubecast Fetch was canceled. {e.args[0]}",
            ) from e

    if video.media_url is None:
        msg = f"The server has not able to fetch a media_url from yt-dlp. {video.id=}"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=msg,
        )

    if handler.USE_PROXY:
        try:
            return await reverse_proxy(url=video.media_url, request=request)
        except Http403ForbiddenError as e:
            logger.error("403 Forbidden. Re-fetching media_url...")
            await fetch_video(video_id=video.id, db=db)
            raise e
        # except HTTPException as e:
        #     # If forbidden 403, try re-fetching again
        #     if e.status_code == status.HTTP_403_FORBIDDEN:
        #         logger.error("403 Forbidden. Re-fetching media_url...")

        #         fetched_video = await fetch_video(video_id=video.id, db=db)

        #         if fetched_video.media_url is None:
        #             msg = f"The server has not able to fetch a media_url from yt-dlp. {video_id=}"
        #             logger.error(msg)
        #             raise HTTPException(
        #                 status_code=status.HTTP_202_ACCEPTED,
        #                 detail=msg,
        #             )

        #         return await reverse_proxy(url=fetched_video.media_url, request=request)

        #     raise e
    return RedirectResponse(url=video.media_url)
