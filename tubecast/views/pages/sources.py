from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlmodel import Session

from tubecast import crud, models
from tubecast.views import deps, templates

router = APIRouter()


@router.get("/sources", response_class=HTMLResponse)
async def list_sources(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    Returns HTML response with list of sources.

    Args:
        request(Request): The request object
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: HTML page with the sources
    """
    # Get alerts dict from cookies
    alerts = models.Alerts().from_cookies(request.cookies)

    sources = await crud.source.get_multi(db=db, created_by=current_user.id)
    return templates.TemplateResponse(
        "source/list.html",
        {"request": request, "sources": sources, "current_user": current_user, "alerts": alerts},
    )


@router.get("/sources/all", response_class=HTMLResponse)
async def list_all_sources(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_superuser
    ),
) -> Response:
    """
    Returns HTML response with list of all sources from all users.

    Args:
        request(Request): The request object
        db(Session): The database session.
        current_user(User): The authenticated superuser.

    Returns:
        Response: HTML page with the sources

    """
    # Get alerts dict from cookies
    alerts = models.Alerts().from_cookies(request.cookies)

    sources = await crud.source.get_all(db=db)
    return templates.TemplateResponse(
        "source/list.html",
        {"request": request, "sources": sources, "current_user": current_user, "alerts": alerts},
    )


@router.get("/source/{source_id}", response_class=HTMLResponse)
async def view_source(
    request: Request,
    source_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    View source.

    Args:
        request(Request): The request object
        source_id(str): The source id
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: View of the source
    """
    alerts = models.Alerts()
    try:
        source = await crud.source.get(db=db, id=source_id)
    except crud.RecordNotFoundError:
        alerts.danger.append("Source not found")
        response = RedirectResponse("/sources", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response

    return templates.TemplateResponse(
        "source/view.html",
        {"request": request, "source": source, "current_user": current_user, "alerts": alerts},
    )


@router.get("/sources/create", response_class=HTMLResponse)
async def create_source(
    request: Request,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    New Source form.

    Args:
        request(Request): The request object
        current_user(User): The authenticated user.

    Returns:
        Response: Form to create a new source
    """
    alerts = models.Alerts().from_cookies(request.cookies)
    return templates.TemplateResponse(
        "source/create.html",
        {"request": request, "current_user": current_user, "alerts": alerts},
    )


@router.post("/sources/create", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
async def handle_create_source(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    Handles the creation of a new source.

    Args:
        background_tasks(BackgroundTasks): The background tasks
        url(str): The url of the source
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: List of sources view
    """
    alerts = models.Alerts()
    try:
        source = await crud.source.create_source_from_url(url=url, user_id=current_user.id, db=db)
    except crud.RecordAlreadyExistsError:
        alerts.danger.append("Source already exists")
        response = RedirectResponse("/sources/create", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response

    # Fetch the source videos in the background
    background_tasks.add_task(
        crud.source.fetch_source,
        id=source.id,
        db=db,
    )

    alerts.success.append("Source successfully created")
    response = RedirectResponse(url="/sources", status_code=status.HTTP_303_SEE_OTHER)
    response.headers["Method"] = "GET"
    response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
    return response


@router.get("/source/{source_id}/edit", response_class=HTMLResponse)
async def edit_source(
    request: Request,
    source_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    New Source form.

    Args:
        request(Request): The request object
        source_id(str): The source id
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: Form to create a new source
    """
    alerts = models.Alerts().from_cookies(request.cookies)
    try:
        source = await crud.source.get(db=db, id=source_id)
    except crud.RecordNotFoundError:
        alerts.danger.append("Source not found")
        response = RedirectResponse("/sources", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response
    return templates.TemplateResponse(
        "source/edit.html",
        {"request": request, "source": source, "current_user": current_user, "alerts": alerts},
    )


@router.post("/source/{source_id}/edit", response_class=HTMLResponse)
async def handle_edit_source(
    request: Request,
    source_id: str,
    name: str = Form(...),
    author: str = Form(...),
    logo: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    Handles the creation of a new source.

    Args:
        request(Request): The request object
        source_id(str): The source id
        name(str): The name of the source
        author(str): The author of the source
        logo(str): The logo of the source
        description(str): The description of the source
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: View of the newly created source
    """
    alerts = models.Alerts()
    source_update = models.SourceUpdate(
        name=name, author=author, logo=logo, description=description
    )

    try:
        new_source = await crud.source.update(db=db, obj_in=source_update, id=source_id)
    except crud.RecordNotFoundError:
        alerts.danger.append("Source not found")
        response = RedirectResponse(url="/sources", status_code=status.HTTP_303_SEE_OTHER)
        response.headers["Method"] = "GET"
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response
    alerts.success.append("Source updated")
    return templates.TemplateResponse(
        "source/edit.html",
        {"request": request, "source": new_source, "current_user": current_user, "alerts": alerts},
    )


@router.get("/source/{source_id}/delete", response_class=HTMLResponse)
async def delete_source(
    source_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    New Source form.

    Args:
        source_id(str): The source id
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: Form to create a new source
    """
    alerts = models.Alerts()
    try:
        await crud.source.remove(db=db, id=source_id)
        alerts.success.append("Source deleted")
    except crud.RecordNotFoundError:
        alerts.danger.append("Source not found")
    except crud.DeleteError:
        alerts.danger.append("Error deleting source")

    response = RedirectResponse(url="/sources", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="alerts", value=alerts.json(), max_age=5, httponly=True)
    return response


@router.get("/source/{source_id}/fetch", status_code=status.HTTP_202_ACCEPTED)
async def fetch_source(
    source_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Response:
    """
    Fetches new data from yt-dlp and updates a source on the server.

    Args:
        source_id: The ID of the source to update.
        db(Session): The database session
        background_tasks: The background tasks to run.
        current_user: The current superuser.

    Returns:
        Response: Redirects to the source page.
    """
    alerts = models.Alerts()
    source = await crud.source.get_or_none(id=source_id, db=db)

    if not current_user.is_superuser:
        alerts.danger.append("You are not authorized to do that")
    else:
        if not source:
            alerts.danger.append("Source not found")
        else:
            # Fetch the source videos in the background
            background_tasks.add_task(
                crud.source.fetch_source,
                id=source_id,
                db=db,
            )
            alerts.success.append(f"Fetching source ('{source.name}')")

    response = RedirectResponse(url="/sources", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="alerts", value=alerts.json(), max_age=5, httponly=True)
    return response