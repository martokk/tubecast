from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import crud, models
from app.api import deps
from app.services.feed import build_rss_file, delete_rss_file

router = APIRouter()


@router.put("/{source_id}", response_class=HTMLResponse)
async def build_rss(
    source_id: str,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> Response:
    """
    Builds a new rss file for source_id and returns it as a Response.

    Args:
        source_id(str): The source_id of the source.
        db(Session): The database session.

    Returns:
        Response: The rss file as a Response.

    Raises:
        HTTPException: If the rss file is not found.
    """
    try:
        source = await crud.source.get(id=source_id, db=db)
    except crud.RecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.args) from exc

    rss_file = await build_rss_file(source=source)

    # Serve RSS File as a Response
    content = rss_file.read_text()
    return Response(content)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rss(
    source_id: str,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> None:
    """
    Deletes the .rss file for a feed.

    Args:
        source_id(str): The source_id of the source.
        db(Session): The database session.
        _: models.User: The current active superuser.

    Returns:
        None: None

    Raises:
        HTTPException: If the rss file is not found.
    """
    try:
        source = await crud.source.get(id=source_id, db=db)
    except crud.RecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.args) from exc
    return await delete_rss_file(source_id=source.id)
