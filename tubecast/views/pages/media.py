from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, Response
from sqlmodel import Session

from tubecast import crud, logger
from tubecast.api.deps import get_db
from tubecast.core.proxy import reverse_proxy
from tubecast.handlers import get_handler_from_string

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

    if video.media_url is None:
        logger.error("The server has not yet retrieved a media_url from yt-dlp.")
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="The server has not yet retrieved a media_url from yt-dlp.",
        )
    handler = get_handler_from_string(handler_string=video.handler)
    if handler.USE_PROXY:
        return await reverse_proxy(url=video.media_url, request=request)
    return RedirectResponse(url=video.media_url)
