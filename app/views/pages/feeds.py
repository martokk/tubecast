from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import HTMLResponse

from app.services.feed import get_rss_file

router = APIRouter()


@router.get("/{source_id}", response_class=HTMLResponse)
async def get_rss(source_id: str) -> Response:
    """
    Gets a rss file for source_id and returns it as a Response

    Args:
        source_id(str): The source_id of the source.

    Returns:
        Response: The rss file as a Response.

    Raises:
        HTTPException: If the rss file is not found.
    """
    try:
        rss_file = await get_rss_file(source_id=source_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.args) from exc

    # Serve RSS File as a Response
    content = rss_file.read_text()
    return Response(content)