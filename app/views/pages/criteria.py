from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import ValidationError
from sqlmodel import Session

from app import crud, models
from app.services.feed import build_rss_file
from app.views import deps, templates

router = APIRouter()


@router.post(
    "/filter/{filter_id}/criteria/create",
    response_class=HTMLResponse,
    status_code=status.HTTP_201_CREATED,
)
async def handle_create_criteria(
    background_tasks: BackgroundTasks,
    filter_id: str,
    field: str = Form(...),
    operator: str = Form(...),
    value: str = Form(...),
    unit_of_measure: str = Form(...),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    Handles the creation of a new Criteria.

    Args:
        background_tasks(BackgroundTasks): The background tasks
        filter_id(str): The filter id
        id(str): The criteria id
        field(str): The field of the criteria
        operator(str): The operator of the criteria
        value(str): The value of the criteria
        unit_of_measure(str): The unit of measure of the criteria
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: List of filters view
    """
    alerts = models.Alerts()

    try:
        obj_in = models.CriteriaCreate(
            filter_id=filter_id,
            field=field,
            operator=operator,
            value=value,
            unit_of_measure=unit_of_measure,
        )
    except ValidationError as exc:
        alerts.danger.append(str(exc.args[0][0].exc.args[0]))
        response = RedirectResponse(f"/filter/{filter_id}", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response

    try:
        criteria = await crud.criteria.create(db=db, obj_in=obj_in)
    except ValueError as exc:
        alerts.danger.append(str(exc.args[0]))
        response = RedirectResponse(f"/filter/{filter_id}", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response

    await build_rss_file(filter=criteria.filter)

    alerts.success.append(f"Criteria successfully created.")
    response = RedirectResponse(url=f"/filter/{filter_id}", status_code=status.HTTP_303_SEE_OTHER)
    response.headers["Method"] = "GET"
    response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
    return response


@router.get("/filter/{filter_id}/criteria/{id}/edit", response_class=HTMLResponse)
async def edit_criteria(
    request: Request,
    filter_id: str,
    id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    Edit Criteria form.

    Args:
        request(Request): The request object
        filter_id(str): The filter id
        id(str): The criteria id
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: Form to create a new filter
    """
    alerts = models.Alerts().from_cookies(request.cookies)
    try:
        criteria = await crud.criteria.get(db=db, id=id)
    except crud.RecordNotFoundError:
        alerts.danger.append("Criteria not found")
        response = RedirectResponse(f"/filter/{filter_id}", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response

    # Build the select options
    criteria_field_select = list(attr.value for attr in models.CriteriaField)
    criteria_field_select.remove(criteria.field)

    created_release_operators_select = [models.CriteriaOperator.WITHIN.value]
    duration_operators_select = [
        models.CriteriaOperator.SHORTER_THAN.value,
        models.CriteriaOperator.LONGER_THAN.value,
    ]
    keyword_operators_select = [
        models.CriteriaOperator.MUST_CONTAIN.value,
        models.CriteriaOperator.MUST_NOT_CONTAIN.value,
    ]

    return templates.TemplateResponse(
        "criteria/edit.html",
        {
            "request": request,
            "criteria": criteria,
            "criteria_field_select": criteria_field_select,
            "created_release_operators_select": created_release_operators_select,
            "duration_operators_select": duration_operators_select,
            "keyword_operators_select": keyword_operators_select,
            "current_user": current_user,
            "alerts": alerts,
        },
    )


@router.post("/filter/{filter_id}/criteria/{id}/edit", response_class=HTMLResponse)
async def handle_edit_criteria(
    request: Request,
    filter_id: str,
    id: str,
    field: str = Form(...),
    operator: str = Form(...),
    value: str = Form(...),
    unit_of_measure: str = Form(...),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    Handles editing of a criteria.

    Args:
        request(Request): The request object
        filter_id(str): The filter id
        id(str): The criteria id
        field(str): The field of the criteria
        operator(str): The operator of the criteria
        value(str): The value of the criteria
        unit_of_measure(str): The unit of measure of the criteria
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: Filter view with updated criteria
    """
    alerts = models.Alerts()
    criteria_update = models.CriteriaUpdate(
        field=field, operator=operator, value=value, unit_of_measure=unit_of_measure
    )

    try:
        new_criteria = await crud.criteria.update(db=db, obj_in=criteria_update, id=id)
        alerts.success.append(f"Criteria '{new_criteria.name}' updated")
        await build_rss_file(filter=new_criteria.filter)
    except ValueError as exc:
        alerts.danger.append(str(exc.args[0]))
        response = RedirectResponse(f"/filter/{filter_id}", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
        return response
    except crud.RecordNotFoundError:
        alerts.danger.append("Criteria not found")

    response = RedirectResponse(url=f"/filter/{filter_id}", status_code=status.HTTP_303_SEE_OTHER)
    response.headers["Method"] = "GET"
    response.set_cookie(key="alerts", value=alerts.json(), httponly=True, max_age=5)
    return response


@router.get("/filter/{filter_id}/criteria/{id}/delete", response_class=HTMLResponse)
async def delete_criteria(
    filter_id: str,
    id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        deps.get_current_active_user
    ),
) -> Response:
    """
    Delete a criteria.

    Args:
        filter_id(str): The filter id
        id(str): The criteria id
        db(Session): The database session.
        current_user(User): The authenticated user.

    Returns:
        Response: Filter view with updated criteria
    """
    alerts = models.Alerts()
    try:
        await crud.criteria.remove(db=db, id=id, filter_id=filter_id)
        alerts.success.append("Criteria deleted")
    except crud.RecordNotFoundError:
        alerts.danger.append("Criteria not found")
    except crud.DeleteError:
        alerts.danger.append("Error deleting criteria")

    response = RedirectResponse(url=f"/filter/{filter_id}", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="alerts", value=alerts.json(), max_age=5, httponly=True)
    return response
