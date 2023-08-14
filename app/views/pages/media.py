import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlmodel import Session

from app import crud, logger
from app.api.deps import get_db
from app.core.proxy import Http403ForbiddenError
from app.services.media import get_media_response

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

    # Get Media Response. Retry on Http403ForbiddenError
    MAX_RETRIES = 10
    retries = 0
    while True:
        try:
            return await get_media_response(db=db, video=video, request=request)
        except Http403ForbiddenError as e:
            retries += 1
            logger.error(f"Retrying ({retries}/{MAX_RETRIES})")

            # Sleep before retrying
            if retries < MAX_RETRIES:
                # sleep an additional x seconds after multiple retires
                if retries >= (MAX_RETRIES / 2):
                    await asyncio.sleep(int(retries * 1.5))

                await asyncio.sleep(1)
                continue

            logger.error("Max retries reached for Http403ForbiddenError.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Max retries reached for Http403ForbiddenError.",
            ) from e
