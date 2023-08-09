from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, Response
from sqlmodel import Session

from app import crud, logger
from app.api.deps import get_db
from app.core.proxy import reverse_proxy
from app.handlers import get_handler_from_string
from app.services.fetch import FetchCanceledError, fetch_video
from app.services.ytdlp import AwaitingTranscodingError

router = APIRouter()


@router.get("/{video_id}")
@router.head("/{video_id}")
async def handle_media(video_id: str, request: Request, db: Session = Depends(get_db)) -> Response:
    """
    Handles the repose for a media request by video_id.
    Uses a reverse proxy if required by the handler.

    Args:
        video_id(str): The video_id of the video.
        request(Request): The request object.
        db(Session): The database session.

    Returns:
        Response: The response object.

    Raises:
        HTTPException: If the video_id is not found.
    """
    try:
        video = await crud.video.get(id=video_id, db=db)
    except crud.RecordNotFoundError as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The video_id '{video_id}' was not found.",
        ) from e

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
        msg = f"The server has not able to fetch a media_url from yt-dlp. {video_id=}"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=msg,
        )

    if handler.USE_PROXY:
        try:
            return await reverse_proxy(url=video.media_url, request=request)
        except HTTPException as e:
            # If forbidden 403, try re-fetching again
            if e.status_code == status.HTTP_403_FORBIDDEN:
                logger.error("403 Forbidden. Re-fetching media_url...")

                fetched_video = await fetch_video(video_id=video.id, db=db)

                if fetched_video.media_url is None:
                    msg = f"The server has not able to fetch a media_url from yt-dlp. {video_id=}"
                    logger.error(msg)
                    raise HTTPException(
                        status_code=status.HTTP_202_ACCEPTED,
                        detail=msg,
                    )

                return await reverse_proxy(url=fetched_video.media_url, request=request)

            raise e
    return RedirectResponse(url=video.media_url)
