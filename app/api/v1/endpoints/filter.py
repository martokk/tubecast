from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import crud, models
from app.api import deps
from app.services.feed import build_rss_file, delete_rss_file

router = APIRouter()
ModelClass = models.Filter
ModelReadClass = models.FilterRead
ModelCreateClass = models.FilterCreate
ModelUpdateClass = models.FilterUpdate
model_crud = crud.filter


@router.post(
    "/source/{source_id}/filter",
    response_model=ModelReadClass,
    status_code=status.HTTP_201_CREATED,
)
async def create_filter(
    *,
    db: Session = Depends(deps.get_db),
    source_id: str,
    obj_in: ModelCreateClass,
    current_active_user: models.User = Depends(deps.get_current_active_user),
) -> ModelClass:
    """
    Create a new filter.

    Args:
        db (Session): database session.
        source_id (str): id of the source.
        obj_in (ModelCreateClass): object to be created.
        current_active_user (models.User): Current active user.

    Returns:
        ModelClass: Created object.

    Raises:
        HTTPException: if object already exists.
    """
    return await model_crud.create(
        db=db, obj_in=obj_in, source_id=source_id, created_by=current_active_user.id
    )


@router.get("/filter/{id}", response_model=ModelReadClass)
async def get(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> ModelClass:
    """
    Retrieve a filter by id.

    Args:
        id (str): id of the filter.
        db (Session): database session.
        current_user (Any): authenticated user.

    Returns:
        ModelClass: Retrieved object.

    Raises:
        HTTPException: if object does not exist.
        HTTPException: if user is not superuser and object does not belong to user.
    """
    _filter = await model_crud.get_or_none(id=id, db=db)
    if _filter:
        if crud.user.is_superuser(user_=current_user) or _filter.created_by == current_user.id:
            return _filter

    elif crud.user.is_superuser(user_=current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filter not found")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


@router.patch("/filter/{id}", response_model=ModelReadClass)
async def update(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    obj_in: ModelUpdateClass,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> ModelClass:
    """
    Update an filter.

    Args:
        id (str): ID of the filter to update.
        obj_in (ModelUpdateClass): object to update.
        db (Session): database session.
        current_user (Any): authenticated user.

    Returns:
        ModelClass: Updated object.

    Raises:
        HTTPException: if object not found.
    """
    _filter = await model_crud.get_or_none(id=id, db=db)
    if _filter:
        if crud.user.is_superuser(user_=current_user) or _filter.created_by == current_user.id:
            return await model_crud.update(db=db, obj_in=obj_in, id=id)

    elif crud.user.is_superuser(user_=current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filter not found")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


@router.delete("/filter/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> None:
    """
    Delete an filter.

    Args:
        id (str): ID of the filter to delete.
        db (Session): database session.
        current_user (models.User): authenticated user.

    Returns:
        None

    Raises:
        HTTPException: if filter not found.
    """

    _filter = await model_crud.get_or_none(id=id, db=db)
    if _filter:
        if crud.user.is_superuser(user_=current_user) or _filter.created_by == current_user.id:
            return await model_crud.remove(id=id, db=db)

    elif crud.user.is_superuser(user_=current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filter not found")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


@router.put("/filter/{id}/feed", response_class=HTMLResponse)
async def build_filter_rss(
    id: str,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> Response:
    """
    Builds a new rss file for filter and returns it as a Response.

    Args:
        id(str): The filter id
        db(Session): The database session.

    Returns:
        Response: The rss file as a Response.

    Raises:
        HTTPException: If the rss file is not found.
    """
    try:
        filter = await crud.filter.get(id=id, db=db)
    except crud.RecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.args) from exc

    rss_file = await build_rss_file(filter=filter)

    # Serve RSS File as a Response
    content = rss_file.read_text()
    return Response(content)
