from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlmodel import Session

from app import crud, models
from app.api import deps
from app.services.source import fetch_all_sources, fetch_source

router = APIRouter()
ModelClass = models.Source
ModelReadClass = models.SourceRead
ModelCreateClass = models.SourceCreate
ModelUpdateClass = models.SourceUpdate
model_crud = crud.source


@router.post("/", response_model=ModelReadClass, status_code=status.HTTP_201_CREATED)
async def create_source_from_url(
    *,
    db: Session = Depends(deps.get_db),
    obj_in: ModelCreateClass,
    background_tasks: BackgroundTasks,
    current_active_user: models.User = Depends(deps.get_current_active_user),
) -> ModelClass:
    """
    Create a new source.

    Args:
        db (Session): database session.
        obj_in (ModelCreateClass): object to create.
        background_tasks (BackgroundTasks): background tasks.
        current_active_user (models.User): current active user.

    Returns:
        ModelClass: Created object.

    Raises:
        HTTPException: if object already exists.
    """
    try:
        source = await crud.source.create_source_from_url(
            url=obj_in.url, user_id=current_active_user.id, db=db
        )
    except crud.RecordAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_200_OK, detail="Source already exists") from exc

    # Fetch the source videos in the background
    background_tasks.add_task(
        fetch_source,
        id=source.id,
        db=db,
    )
    return source


@router.get("/{id}", response_model=ModelReadClass)
async def get(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> ModelClass:
    """
    Retrieve a source by id.

    Args:
        id (str): id of the source.
        db (Session): database session.
        current_user (Any): authenticated user.

    Returns:
        ModelClass: Retrieved object.

    Raises:
        HTTPException: if object does not exist.
        HTTPException: if user is not superuser and object does not belong to user.
    """
    source = await model_crud.get_or_none(id=id, db=db)
    if source:
        if crud.user.is_superuser(user_=current_user) or source.created_by == current_user.id:
            return source

    elif crud.user.is_superuser(user_=current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
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
    Retrieve sources.

    Args:
        db (Session): database session.
        skip (int): Number of sources to skip. Defaults to 0.
        limit (int): Number of sources to return. Defaults to 100.
        current_user (models.User): Current active user.

    Returns:
        list[ModelClass]: List of objects.
    """
    return (
        await model_crud.get_multi(db=db, skip=skip, limit=limit)
        if crud.user.is_superuser(user_=current_user)
        else await model_crud.get_multi(db=db, created_by=current_user.id, skip=skip, limit=limit)
    )


@router.get("/{id}/videos", response_model=list[models.VideoRead])
async def get_videos_from_source(
    id: str,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> list[models.Video]:
    """
    Retrieve videos from a source.

    Args:
        id (str): id of the source.
        db (Session): database session.
        skip (int): Number of items to skip. Defaults to 0.
        limit (int): Number of items to return. Defaults to 100.
        current_user (models.User): Current active user.

    Returns:
        list[ModelClass]: List of objects.

    Raises:
        HTTPException: if user is not superuser and object does not belong to user.
    """
    source = await crud.source.get(db=db, id=id)
    if crud.user.is_superuser(user_=current_user) or source.created_by == current_user.id:
        return await crud.video.get_multi(db=db, source_id=id, skip=skip, limit=limit)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


@router.patch("/{id}", response_model=ModelReadClass)
async def update(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    obj_in: ModelUpdateClass,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> ModelClass:
    """
    Update an source.

    Args:
        id (str): ID of the source to update.
        obj_in (ModelUpdateClass): object to update.
        db (Session): database session.
        current_user (Any): authenticated user.

    Returns:
        ModelClass: Updated object.

    Raises:
        HTTPException: if object not found.
    """
    source = await model_crud.get_or_none(id=id, db=db)
    if source:
        if crud.user.is_superuser(user_=current_user) or source.created_by == current_user.id:
            return await model_crud.update(db=db, obj_in=obj_in, id=id)

    elif crud.user.is_superuser(user_=current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> None:
    """
    Delete an source.

    Args:
        id (str): ID of the source to delete.
        db (Session): database session.
        current_user (models.User): authenticated user.

    Returns:
        None

    Raises:
        HTTPException: if source not found.
    """

    source = await model_crud.get_or_none(id=id, db=db)
    if source:
        if crud.user.is_superuser(user_=current_user) or source.created_by == current_user.id:
            return await model_crud.remove(id=id, db=db)

    elif crud.user.is_superuser(user_=current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


@router.put("/{id}/fetch", status_code=status.HTTP_202_ACCEPTED)
async def fetch_source_endpoint(
    id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> None:
    """
    Fetches new data from yt-dlp and updates a source on the server.

    Args:
        id: The ID of the source to update.
        db(Session): The database session
        background_tasks: The background tasks to run.
        _: The current superuser.

    Raises:
        HTTPException: If the source was not found.
    """

    try:
        source = await crud.source.get(id=id, db=db)
    except crud.RecordNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source Not Found"
        ) from exc

    # Fetch the source videos in the background
    background_tasks.add_task(
        fetch_source,
        id=source.id,
        db=db,
    )


@router.put("/fetch", status_code=status.HTTP_202_ACCEPTED, response_model=models.Msg)
async def fetch_all(
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> dict[str, str]:
    """
    Fetches new data from yt-dlp for all sources on the server.

    Args:
        background_tasks: The background tasks to run.
        db(Session): The database session
        _: The current superuser.

    """
    # Fetch the source videos in the background
    background_tasks.add_task(fetch_all_sources, db=db)

    return {"msg": "Fetching all sources in the background."}
