from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response
from sqlmodel import Session

from python_fastapi_stack import crud, models
from python_fastapi_stack.views import deps, templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def user_account(
    request: Request,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Response:
    """
    Display the users account page.

    Args:
        request(Request): The request object
        current_user(models.User): The current user

    Returns:
        Response: The users account page
    """
    context = {"request": request, "current_user": current_user, "db_user": current_user}
    return templates.TemplateResponse("user/view.html", context=context)


@router.get("/edit", response_class=HTMLResponse)
async def edit_user_account(
    request: Request,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Response:
    """
    Display the users account edit page.

    Args:
        request(Request): The request object
        current_user(models.User): The current user

    Returns:
        Response: The users account page
    """
    alerts = models.Alerts().from_cookies(request.cookies)
    context = {
        "request": request,
        "current_user": current_user,
        "db_user": current_user,
        "alerts": alerts,
    }
    return templates.TemplateResponse("user/edit.html", context=context)


@router.post("/edit", response_class=HTMLResponse)
async def update_user_account(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    full_name: str = Form(...),
    email: str = Form(...),
    is_active: bool | None = Form(None),
    is_superuser: bool | None = Form(None),
) -> Response:
    """
    Update the users account.

    Args:
        request(Request): The request object
        db(Session): The database session.
        current_user(models.User): The current user
        full_name(str): The users full name
        email(str): The users email
        is_active(bool): Is the user active
        is_superuser(bool): Is the user a superuser

    Returns:
        Response: The users account page
    """
    alerts = models.Alerts()
    if current_user.is_superuser:
        user_update = models.UserUpdate(
            full_name=full_name, email=email, is_active=is_active, is_superuser=is_superuser
        )
    else:
        user_update = models.UserUpdate(full_name=full_name, email=email)

    db_user = await crud.user.update(db=db, obj_in=user_update, id=current_user.id)

    alerts.success.append("User updated successfully")
    context = {"request": request, "current_user": db_user, "db_user": db_user, "alerts": alerts}
    return templates.TemplateResponse("user/edit.html", context=context)
