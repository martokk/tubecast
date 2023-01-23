from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from tubecast import crud
from tubecast.api.deps import get_db

router = APIRouter()
templates = Jinja2Templates(directory="tubecast/views/templates")


@router.get(
    "/sources", summary="Returns HTML Response with the source", response_class=HTMLResponse
)
async def html_view_sources(request: Request, db: Session = Depends(get_db)) -> Response:
    """
    Returns HTML response with list of sources.

    Args:
        request(Request): The request object
        db(Session): The database session.

    Returns:
        Response: HTML page with the sources

    """
    sources = await crud.source.get_all(db=db)
    sources_context = [
        {
            "id": source.id,
            "title": source.title,
            "url": source.url,
        }
        for source in sources
    ]
    context = {"request": request, "sources": sources_context}
    return templates.TemplateResponse("view_sources.html", context)
