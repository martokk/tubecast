from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from tubecast import models, settings
from tubecast.views import deps, templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root_index_router(
    request: Request,
    current_user: models.User = Depends(deps.get_current_user),
) -> Response:
    """
    Home page router

    Args:
        request(Request): The request object
        current_user(models.User): The current user

    Returns:
        Response: Home page
    """
    if current_user:
        return await root_index_authenticated(request, current_user)
    return await root_index_unauthenticated()


async def root_index_unauthenticated() -> Response:
    """
    Home page (Not authenticated)

    Returns:
        Response: Home page
    """
    return RedirectResponse(url="/login")


async def root_index_authenticated(
    request: Request,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Response:
    """
    Home page. (Authenticated)

    Args:
        request(Request): The request object
        current_user(models.User): The current user

    Returns:
        Response: Home page
    """
    alerts = models.Alerts().from_cookies(request.cookies)
    title = f"{settings.PROJECT_NAME} - Home"
    message = f"Welcome to the {settings.PROJECT_NAME}, {current_user.username}!"
    context = {
        "request": request,
        "current_user": current_user,
        "title": title,
        "message": message,
        "alerts": alerts,
    }
    return templates.TemplateResponse("root/home.html", context=context)
