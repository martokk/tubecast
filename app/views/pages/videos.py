from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlmodel import Session

from app import crud, models
from app.services.fetch import FetchCanceledError, fetch_video
from app.views import deps, templates

router = APIRouter()


@router.get("/source/{source_id}/video/{video_id}", response_class=HTMLResponse)
@router.get("/video/{video_id}", response_class=HTMLResponse)
async def view_video(
    request: Request,
    video_id: str,
    source_id: str | None = None,
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
    alerts = models.Alerts().from_cookies(request.cookies)
    try:
        video = await crud.video.get(db=db, id=video_id)
    except crud.RecordNotFoundError:
        alerts.danger.append("Video not found")
        response = RedirectResponse("/sources", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response
    video.description = str(video.description).replace("\n", "<br>")

    source = await crud.source.get_or_none(db=db, id=source_id) if source_id else None

    return templates.TemplateResponse(
        "video/view.html",
        {
            "request": request,
            "video": video,
            "source": source,
            "current_user": current_user,
            "alerts": alerts,
        },
    )


@router.get("/video/{video_id}/fetch", status_code=status.HTTP_202_ACCEPTED)
async def fetch_video_page(
    video_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Response:
    """
    Fetches new data from yt-dlp and updates a video on the server.

    Args:
        video_id: The ID of the video to update.
        db(Session): The database session
        background_tasks: The background tasks to run.
        current_user: The current superuser.

    Returns:
        Response: Redirects to the video page.
    """
    alerts = models.Alerts()
    video = await crud.video.get_or_none(id=video_id, db=db)

    if not current_user.is_superuser:
        alerts.danger.append("You are not authorized to do that")
    elif not video:
        alerts.danger.append("Video not found")
    else:
        try:
            await fetch_video(video_id=video_id, db=db)
            alerts.success.append(f"Video '{video.title}' was fetched.")
        except FetchCanceledError as e:
            alerts.danger.append(f"Fetch canceled. {e}")

    response = RedirectResponse(
        url=f"/video/{video.id}" if video else "/", status_code=status.HTTP_303_SEE_OTHER
    )
    response.set_cookie(key="alerts", value=alerts.json(), max_age=5, httponly=True)
    return response
