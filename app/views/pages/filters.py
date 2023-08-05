from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlmodel import Session

from app import crud, logger, models
from app.core.notify import notify
from app.models.source_video_link import SourceOrderBy
from app.services.feed import build_rss_file, delete_rss_file, get_rss_file
from app.services.fetch import FetchCanceledError, fetch_source
from app.views import deps, templates

router = APIRouter()


@router.post(
    "/source/{source_id}/filter/create",
    response_class=HTMLResponse,
    status_code=status.HTTP_201_CREATED,
)
async def handle_create_filter(
    background_tasks: BackgroundTasks,
    source_id: str,
    name: str = Form(None),
    ordered_by: str = Form(None),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    Handles the creation of a new filter.

    Args:
        background_tasks(BackgroundTasks): The background tasks
        name(str): The name of the filter
        source_id(str): The id of the source
        ordered_by(str): The order of the filter
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: List of filters view
    """
    alerts = models.Alerts()

    source = await crud.source.get(db=db, id=source_id)
    obj_in = models.FilterCreate(
        name=name, source_id=source.id, ordered_by=source.ordered_by, created_by=current_user.id
    )
    if not name:
        alerts.danger.append("Filter name is required.")
        redirect_url = f"/source/{source.id}"
    else:
        _filter = await crud.filter.create(db=db, obj_in=obj_in)
        await build_rss_file(filter=_filter)
        alerts.success.append(f"Filter '{_filter.name}' successfully created.")
        redirect_url = f"/filter/{_filter.id}"

    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    response.headers["Method"] = "GET"
    response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
    return response


@router.get("/filter/{filter_id}", response_class=HTMLResponse)
async def view_filter(
    request: Request,
    filter_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    View filter.

    Args:
        request(Request): The request object
        filter_id(str): The id of the filter
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: View of the filter
    """
    alerts = models.Alerts().from_cookies(request.cookies)
    try:
        _filter = await crud.filter.get(db=db, id=filter_id)
    except crud.RecordNotFoundError:
        alerts.danger.append("Filter not found")
        response = RedirectResponse("/sources", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response

    # Build the select options
    criteria_field_select = list(attr.value for attr in models.CriteriaField)
    created_release_operators_select = [models.CriteriaOperator.WITHIN.value]
    duration_operators_select = [
        models.CriteriaOperator.SHORTER_THAN.value,
        models.CriteriaOperator.LONGER_THAN.value,
    ]
    keyword_operators_select = [
        models.CriteriaOperator.MUST_CONTAIN.value,
        models.CriteriaOperator.MUST_NOT_CONTAIN.value,
    ]

    ordered_by_select = list(attr.value for attr in SourceOrderBy)

    return templates.TemplateResponse(
        "filter/view.html",
        {
            "request": request,
            "filter": _filter,
            "ordered_by_select": ordered_by_select,
            "criteria_field_select": criteria_field_select,
            "created_release_operators_select": created_release_operators_select,
            "duration_operators_select": duration_operators_select,
            "keyword_operators_select": keyword_operators_select,
            "current_user": current_user,
            "alerts": alerts,
        },
    )


@router.get("/filter/{filter_id}/edit", response_class=HTMLResponse)
async def edit_filter(
    request: Request,
    filter_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    New Source Filter form.

    Args:
        request(Request): The request object
        filter_id(str): The filter id
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: Form to create a new filter
    """
    alerts = models.Alerts().from_cookies(request.cookies)
    try:
        filter = await crud.filter.get(db=db, id=filter_id)
    except crud.RecordNotFoundError:
        alerts.danger.append("Filter not found")
        response = RedirectResponse("/sources", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response

    ordered_by_select = list(attr.value for attr in SourceOrderBy)

    return templates.TemplateResponse(
        "filter/edit.html",
        {
            "request": request,
            "filter": filter,
            "ordered_by_select": ordered_by_select,
            "current_user": current_user,
            "alerts": alerts,
        },
    )


@router.post("/filter/{filter_id}/edit", response_class=HTMLResponse)
async def handle_edit_filter(
    request: Request,
    filter_id: str,
    name: str = Form(None),
    source_id: str = Form(None),
    ordered_by: str = Form(None),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    Handles the creation of a new filter.

    Args:
        request(Request): The request object
        filter_id(str): The filter id
        name(str): The name of the filter
        source_id(str): The id of the source
        ordered_by(str): The order by value
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: View of the newly created filter
    """
    alerts = models.Alerts()
    filter_update = models.FilterUpdate(name=name, source_id=source_id, ordered_by=ordered_by)

    try:
        new_filter = await crud.filter.update(
            db=db, obj_in=filter_update, exclude_none=True, id=filter_id
        )
        await build_rss_file(filter=new_filter)
        alerts.success.append(f"Source Filter '{new_filter.name}' updated")
        return_url = f"/filter/{new_filter.id}"
    except crud.RecordNotFoundError:
        alerts.danger.append("Filter not found")
        return_url = "/sources"

    response = RedirectResponse(url=return_url, status_code=status.HTTP_303_SEE_OTHER)
    response.headers["Method"] = "GET"
    response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
    return response


@router.get("/filter/{filter_id}/delete", response_class=HTMLResponse)
async def delete_filter(
    filter_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    New Source Filter form.

    Args:
        filter_id(str): The filter id
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: Form to create a new filter
    """
    alerts = models.Alerts()
    try:
        _filter = await crud.filter.get(db=db, id=filter_id)
        _filter = _filter.copy()
        await crud.filter.remove(db=db, id=filter_id)
        try:
            await delete_rss_file(id=filter_id)
        except FileNotFoundError:
            pass
        alerts.success.append(f"Filter '{_filter.name}' deleted")
        return_url = f"/source/{_filter.source_id}"
    except crud.RecordNotFoundError:
        alerts.danger.append(f"Filter not found")
        return_url = f"/filter/{filter_id}"
    except crud.DeleteError:
        alerts.danger.append("Error deleting filter")
        return_url = f"/filter/{filter_id}"

    response = RedirectResponse(url=return_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="alerts", value=alerts.json(), max_age=5, httponly=True)
    return response


@router.get("/filter/{filter_id}/fetch", status_code=status.HTTP_202_ACCEPTED)
async def fetch_filter_page(
    filter_id: str,
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
        Response: Redirects to the filter page or the sources page.
    """
    alerts = models.Alerts()
    filter = await crud.filter.get_or_none(id=filter_id, db=db)

    if not current_user.is_superuser:
        alerts.danger.append("You are not authorized to do that")
    elif not filter:
        alerts.danger.append("Filter not found")
    else:
        try:
            await fetch_source(db=db, id=filter.source.id)
            alerts.success.append(f"Filter '{filter.name}' was fetched.")
        except FetchCanceledError:
            alerts.danger.append(f"Fetch of filter '{filter.name}' was cancelled.")

    response = RedirectResponse(
        url=f"/filter/{filter.id}" if filter else "/sources", status_code=status.HTTP_303_SEE_OTHER
    )
    response.set_cookie(key="alerts", value=alerts.json(), max_age=5, httponly=True)
    return response


@router.get("/filter/{filter_id}/feed", response_class=HTMLResponse)
async def get_filter_rss_feed(filter_id: str, db: Session = Depends(deps.get_db)) -> Response:
    """
    Gets a rss file for filter_id and returns it as a Response

    Args:
        filter_id(str): The filter_id of the filter.

    Returns:
        Response: The rss file as a Response.

    Raises:
        HTTPException: If the rss file is not found.
    """
    try:
        filter_ = await crud.filter.get(id=filter_id, db=db)
    except crud.RecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=exc.args) from exc

    try:
        rss_file = await get_rss_file(id=filter_.id)
    except FileNotFoundError as exc:
        await build_rss_file(filter=filter_)
        try:
            rss_file = await get_rss_file(id=filter_.id)
        except FileNotFoundError as exc:  # pragma: no cover
            err_msg = f"RSS file ({filter_.id}.rss) does not exist for filter '{filter_.id=}' ({filter_.source.name} - [{filter_.name}]).)"
            logger.critical(err_msg)
            await notify(telegram=True, email=False, text=err_msg)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg) from exc

    # Serve RSS File as a Response
    content = rss_file.read_text()
    return Response(content)
