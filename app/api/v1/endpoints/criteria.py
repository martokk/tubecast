from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app import crud, models
from app.api import deps

router = APIRouter()
ModelClass = models.Criteria
ModelReadClass = models.CriteriaRead
ModelCreateClass = models.CriteriaCreate
ModelUpdateClass = models.CriteriaUpdate
model_crud = crud.criteria


@router.post(
    "/filter/{filter_id}/criteria",
    response_model=ModelReadClass,
    status_code=status.HTTP_201_CREATED,
)
async def create_criteria(
    *,
    db: Session = Depends(deps.get_db),
    filter_id: str,
    obj_in: ModelCreateClass,
    current_active_user: models.User = Depends(deps.get_current_active_user),
) -> ModelClass:
    """
    Create a new criteria.

    Args:
        obj_in (ModelCreateClass): object to be created.
        db (Session): database session.
        current_active_user (models.User): Current active user.

    Returns:
        ModelClass: Created object.
    """
    return await model_crud.create(db=db, obj_in=obj_in, filter_id=filter_id)


@router.get("/criteria/{id}", response_model=ModelReadClass)
async def get(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> ModelClass:
    """
    Retrieve a criteria by id.

    Args:
        id (str): id of the criteria.
        db (Session): database session.
        current_user (Any): authenticated user.

    Returns:
        ModelClass: Retrieved object.

    Raises:
        HTTPException: if object does not exist.
        HTTPException: if user is not superuser and object does not belong to user.
    """
    _criteria = await model_crud.get_or_none(id=id, db=db)
    if _criteria:
        if (
            crud.user.is_superuser(user_=current_user)
            or _criteria.filter.created_by == current_user.id
        ):
            return _criteria

    elif crud.user.is_superuser(user_=current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Criteria not found")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


@router.patch("/criteria/{id}", response_model=ModelReadClass)
async def update(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    obj_in: ModelUpdateClass,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> ModelClass:
    """
    Update an criteria.

    Args:
        id (str): ID of the criteria to update.
        obj_in (ModelUpdateClass): object to update.
        db (Session): database session.
        current_user (Any): authenticated user.

    Returns:
        ModelClass: Updated object.

    Raises:
        HTTPException: if object not found.
    """
    _criteria = await model_crud.get_or_none(id=id, db=db)
    if _criteria:
        if (
            crud.user.is_superuser(user_=current_user)
            or _criteria.filter.created_by == current_user.id
        ):
            try:
                return await model_crud.update(db=db, obj_in=obj_in, id=id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    elif crud.user.is_superuser(user_=current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Criteria not found")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


@router.delete("/criteria/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> None:
    """
    Delete an criteria.

    Args:
        id (str): ID of the criteria to delete.
        db (Session): database session.
        current_user (models.User): authenticated user.

    Returns:
        None

    Raises:
        HTTPException: if criteria not found.
    """

    _criteria = await model_crud.get_or_none(id=id, db=db)
    if _criteria:
        if (
            crud.user.is_superuser(user_=current_user)
            or _criteria.filter.created_by == current_user.id
        ):
            return await model_crud.remove(id=id, db=db)

    elif crud.user.is_superuser(user_=current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Criteria not found")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
