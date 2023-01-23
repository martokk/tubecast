from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from tubecast import crud, models
from tubecast.api import deps

router = APIRouter()
ModelClass = models.source
ModelReadClass = models.SourceRead
ModelCreateClass = models.SourceCreate
ModelUpdateClass = models.SourceUpdate
model_crud = crud.source


@router.post("/", response_model=ModelReadClass, status_code=status.HTTP_201_CREATED)
async def create_with_uploader_id(
    *,
    db: Session = Depends(deps.get_db),
    in_obj: ModelCreateClass,
    current_active_user: models.User = Depends(deps.get_current_active_user),
) -> ModelClass:
    """
    Create a new item.

    Args:
        in_obj (ModelCreateClass): object to be created.
        db (Session): database session.
        current_active_user (models.User): Current active user.

    Returns:
        ModelClass: Created object.

    Raises:
        HTTPException: if object already exists.
    """
    try:
        return await model_crud.create_with_owner_id(
            db=db, in_obj=in_obj, owner_id=current_active_user.id
        )
    except crud.RecordAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_200_OK, detail="source already exists") from exc


@router.get("/{id}", response_model=ModelReadClass)
async def get(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> ModelClass:
    """
    Retrieve a item by id.

    Args:
        id (str): id of the item.
        db (Session): database session.
        current_user (Any): authenticated user.

    Returns:
        ModelClass: Retrieved object.

    Raises:
        HTTPException: if object does not exist.
        HTTPException: if user is not superuser and object does not belong to user.
    """
    source = await model_crud.get_or_none(id=id, db=db)
    if not source:
        if crud.user.is_superuser(user_=current_user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="source not found")
    else:
        if crud.user.is_superuser(user_=current_user) or source.owner_id == current_user.id:
            return source

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


@router.get("/", response_model=list[ModelReadClass])
async def get_multi(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> list[ModelClass]:
    """
    Retrieve items.

    Args:
        db (Session): database session.
        skip (int): Number of items to skip. Defaults to 0.
        limit (int): Number of items to return. Defaults to 100.
        current_user (models.User): Current active user.

    Returns:
        list[ModelClass]: List of objects.
    """
    if crud.user.is_superuser(user_=current_user):
        items = await model_crud.get_multi(db=db, skip=skip, limit=limit)
    else:
        items = await model_crud.get_multi_by_owner_id(
            db=db, owner_id=current_user.id, skip=skip, limit=limit
        )
    return items


@router.patch("/{id}", response_model=ModelReadClass)
async def update(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    in_obj: ModelUpdateClass,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> ModelClass:
    """
    Update an item.

    Args:
        id (str): ID of the item to update.
        in_obj (ModelUpdateClass): object to update.
        db (Session): database session.
        current_user (Any): authenticated user.

    Returns:
        ModelClass: Updated object.

    Raises:
        HTTPException: if object not found.
    """
    source = await model_crud.get_or_none(id=id, db=db)
    if not source:
        if crud.user.is_superuser(user_=current_user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="source not found")
    else:
        if crud.user.is_superuser(user_=current_user) or source.owner_id == current_user.id:
            return await model_crud.update(db=db, in_obj=in_obj, id=id)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> None:
    """
    Delete an item.

    Args:
        id (str): ID of the item to delete.
        db (Session): database session.
        current_user (models.User): authenticated user.

    Returns:
        None

    Raises:
        HTTPException: if item not found.
    """

    source = await model_crud.get_or_none(id=id, db=db)
    if not source:
        if crud.user.is_superuser(user_=current_user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="source not found")
    else:
        if crud.user.is_superuser(user_=current_user) or source.owner_id == current_user.id:
            return await model_crud.remove(id=id, db=db)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
