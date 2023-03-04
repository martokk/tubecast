from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlmodel import Session

from app import crud, models
from app.views import deps, templates

router = APIRouter()


@router.get("/video/{video_id}", response_class=HTMLResponse)
async def view_video(
    request: Request,
    video_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    View video.

    Args:
        request(Request): The request object
        video_id(str): The video id
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: View of the video
    """
    alerts = models.Alerts()
    try:
        video = await crud.video.get(db=db, id=video_id)
    except crud.RecordNotFoundError:
        alerts.danger.append("Video not found")
        response = RedirectResponse("/sources", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response
    video.description = str(video.description).replace("\n", "<br>")
    return templates.TemplateResponse(
        "video/view.html",
        {"request": request, "video": video, "current_user": current_user, "alerts": alerts},
    )
