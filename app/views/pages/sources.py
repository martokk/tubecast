from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlmodel import Session

from app import crud, logger, models
from app.core.notify import notify
from app.handlers.exceptions import HandlerNotFoundError, InvalidSourceUrl
from app.services.feed import build_rss_file, get_rss_file
from app.services.fetch import FetchCanceledError, fetch_all_sources, fetch_source
from app.services.ytdlp import NoUploadsError, PlaylistNotFoundError
from app.views import deps, templates

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

    return templates.TemplateResponse(
        "source/list.html",
        {
            "request": request,
            "sources": current_user.sources,
            "current_user": current_user,
            "alerts": alerts,
        },
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
    alerts = models.Alerts().from_cookies(request.cookies)
    try:
        source = await crud.source.get(db=db, id=source_id)
    except crud.RecordNotFoundError:
        alerts.danger.append("Source not found")
        response = RedirectResponse("/sources", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response

    if source not in current_user.sources and not current_user.is_superuser:
        alerts.danger.append("You do not have access to this source")
        response = RedirectResponse("/sources", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response

    source.description = str(source.description).replace("\n", "<br>")
    return templates.TemplateResponse(
        "source/view.html",
        {"request": request, "source": source, "current_user": current_user, "alerts": alerts},
    )


# @router.get("/sources/create", response_class=HTMLResponse)
# async def create_source(
#     request: Request,
#     current_user: models.User = Depends(  # pylint: disable=unused-argument
#         deps.get_current_active_user
#     ),
# ) -> Response:
#     """
#     New Source form.

#     Args:
#         request(Request): The request object
#         current_user(User): The authenticated user.

#     Returns:
#         Response: Form to create a new source
#     """
#     alerts = models.Alerts().from_cookies(request.cookies)
#     return templates.TemplateResponse(
#         "source/create.html",
#         {"request": request, "current_user": current_user, "alerts": alerts},
#     )


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
    except (
        crud.RecordAlreadyExistsError,
        NoUploadsError,
        HandlerNotFoundError,
        InvalidSourceUrl,
    ) as exc:
        alerts.danger.append(str(exc))
        response = RedirectResponse("/sources", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response

    # Fetch the source videos in the background
    background_tasks.add_task(
        fetch_source,
        id=source.id,
        db=db,
    )

    alerts.success.append(f"{source.service.title()} source '{source.name}' successfully created.")
    response = RedirectResponse(url=f"/source/{source.id}", status_code=status.HTTP_303_SEE_OTHER)
    response.headers["Method"] = "GET"
    response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
    return response


@router.get("/source/{source_id}/edit", response_class=HTMLResponse)
async def edit_source(
    request: Request,
    source_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_superuser
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
    background_tasks: BackgroundTasks,
    name: str = Form(None),
    author: str = Form(None),
    logo: str = Form(None),
    description: str = Form(None),
    reverse_import_order: bool = Form(False),
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
        background_tasks(BackgroundTasks): The background tasks
        name(str): The name of the source
        author(str): The author of the source
        logo(str): The logo of the source
        description(str): The description of the source
        reverse_import_order(bool): The reverse import order of the source
        db(Session): The database session.
        current_user(User): The authenticated user.


    Returns:
        Response: View of the newly created source
    """
    alerts = models.Alerts()
    try:
        db_source = await crud.source.get(db=db, id=source_id)
    except crud.RecordNotFoundError:
        alerts.danger.append(f"Source '{source_id}' not found")
        redirect_url = "/sources"
        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response

    db_reverse_import_order = db_source.reverse_import_order
    source_update = models.SourceUpdate(
        name=name,
        author=author,
        logo=logo,
        description=description,
        reverse_import_order=reverse_import_order,
    )

    new_source = await crud.source.update(
        db=db, obj_in=source_update, id=source_id, exclude_none=True, exclude_unset=True
    )
    alerts.success.append(f"Updated source '{new_source.name}'")
    redirect_url = f"/source/{new_source.id}"

    # If the reverse import order has changed, re-fetch the source
    if db_reverse_import_order != reverse_import_order:
        await fetch_source(id=new_source.id, db=db, ignore_video_refresh=True)
        background_tasks.add_task(
            fetch_source,
            id=new_source.id,
            db=db,
        )

    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    response.headers["Method"] = "GET"
    response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
    return response


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

    source = await crud.source.get_or_none(db=db, id=source_id)

    if not source:
        alerts.danger.append("Source not found")
    else:
        # Remove from user's sources
        await crud.user.remove_source(db=db, user_id=current_user.id, source=source)
        alerts.success.append("Source removed from user.")

        # Remove source if no users
        if len(source.users) == 0:
            try:
                await crud.source.remove(db=db, id=source_id)
                alerts.success.append("Source deleted")
            except crud.DeleteError:
                alerts.danger.append("Error deleting source")

    # Redirect to sources page
    response = RedirectResponse(url="/sources", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="alerts", value=alerts.json(), max_age=5, httponly=True)
    return response


@router.get("/source/{source_id}/fetch", status_code=status.HTTP_202_ACCEPTED)
async def fetch_source_page(
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
    elif not source:
        alerts.danger.append("Source not found")
    else:
        try:
            await fetch_source(db=db, id=source_id)
            alerts.success.append(f"Source '{source.name}' was fetched.")
        except FetchCanceledError:
            alerts.danger.append(f"Fetch of source '{source.name}' was cancelled.")

    response = RedirectResponse(
        url=f"/source/{source.id}" if source else "/sources", status_code=status.HTTP_303_SEE_OTHER
    )
    response.set_cookie(key="alerts", value=alerts.json(), max_age=5, httponly=True)
    return response


@router.get("/sources/fetch", status_code=status.HTTP_202_ACCEPTED)
async def fetch_all_source_page(
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Response:
    """
    Fetches new data from yt-dlp and updates a source on the server.

    Args:
        db(Session): The database session
        background_tasks: The background tasks to run.
        current_user: The current superuser.

    Returns:
        Response: Redirects to the source page.
    """
    alerts = models.Alerts()
    if not current_user.is_superuser:
        alerts.danger.append("You are not authorized to do that")
    else:
        background_tasks.add_task(fetch_all_sources, db=db)
        alerts.success.append(f"Fetching all sources...")

    response = RedirectResponse(url=f"/sources", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="alerts", value=alerts.json(), max_age=5, httponly=True)
    return response


@router.get("/source/{source_id}/feed", response_class=HTMLResponse)
async def get_source_rss_feed(source_id: str, db: Session = Depends(deps.get_db)) -> Response:
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
        rss_file = await get_rss_file(id=source_id)

    except FileNotFoundError as exc:
        # Handle source not found
        try:
            source = await crud.source.get(id=source_id, db=db)
        except crud.RecordNotFoundError as exc:
            err_msg = f"Source '{source_id}' not found."
            logger.critical(err_msg)
            await notify(telegram=True, email=False, text=err_msg)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg) from exc

        # Build and get rss file
        await build_rss_file(source=source)
        try:
            rss_file = await get_rss_file(id=source_id)
        except FileNotFoundError as exc:
            err_msg = (
                f"RSS file ({source.id}.rss) does not exist for '{source.id=}' ({source.name}).)"
            )
            logger.critical(err_msg)
            await notify(telegram=True, email=False, text=err_msg)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg) from exc

    # Serve RSS File as a Response
    content = rss_file.read_text()
    return Response(content)
