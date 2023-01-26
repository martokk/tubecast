from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from tubecast import crud, settings
from tubecast.api import deps

router = APIRouter()
templates = Jinja2Templates(directory="tubecast/views/templates")


@router.get(
    "/u/{username}", summary="Returns HTML Response with list of feeds", response_class=HTMLResponse
)
async def html_view_users_sources(
    request: Request, username: str, db: Session = Depends(deps.get_db)
) -> Response:
    """
    Returns HTML Response with list of feeds for the given user.

    Args:
        request(Request): The request object
        username: The username to display
        db(Session): The database session.

    Returns:
        Response: HTML page with list of sources

    Raises:
        HTTPException: User not found
    """
    try:
        user = await crud.user.get(username=username, db=db)
    except crud.RecordNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from e
    # sources = await source_crud.get_many(created_by=user.id)
    sources_context = [
        {
            "name": source.name,
            "url": source.url,
            "pktc_subscription_url": f"pktc://subscribe/{settings.BASE_DOMAIN}{source.feed_url}",
        }
        for source in user.sources
    ]
    context = {"request": request, "sources": sources_context, "username": username}
    return templates.TemplateResponse("view_users_sources.html", context)
