from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from tubecast import crud, models
from tubecast.api import deps

router = APIRouter()
ModelClass = models.Video
ModelReadClass = models.VideoRead
ModelCreateClass = models.VideoCreate
ModelUpdateClass = models.VideoUpdate
model_crud = crud.video


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
    video = await model_crud.get_or_none(id=id, db=db)
    if not video:
        if crud.user.is_superuser(user_=current_user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="video not found")
    else:
        if crud.user.is_superuser(user_=current_user):
            return video

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


@router.get("/", response_model=list[ModelReadClass])
async def get_multi(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
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
    return await model_crud.get_multi(db=db, skip=skip, limit=limit)


@router.put("/{id}/fetch", response_model=models.VideoRead)
async def fetch_video(
    id: str,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> models.Video:
    """
    Fetches new data from yt-dlp and updates a video on the server.

    Args:
        id: The ID of the video to update.
        db (Session): The database session.
        _ (Any): authenticated user.

    Returns:
        The updated video.

    Raises:
        HTTPException: If the video was not found.
    """
    try:
        return await model_crud.fetch_video(video_id=id, db=db)
    except crud.RecordNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video Not Found"
        ) from exc


@router.put("/fetch", response_model=list[models.VideoRead], status_code=status.HTTP_200_OK)
async def fetch_all(
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> list[models.Video] | None:
    """
    Fetches new data from yt-dlp and updates all videos on the server.

    Args:
        db (Session): The database session.
        _ (Any): authenticated user.

    Returns:
        list[ModelClass]: List of objects.
    """
    return await model_crud.fetch_all_videos(db=db)


# @router.post("/", response_model=ModelReadClass, status_code=status.HTTP_201_CREATED)
# async def create_video_from_url(
#     *,
#     db: Session = Depends(deps.get_db),
#     in_obj: ModelCreateClass,
#     _: models.User = Depends(deps.get_current_active_user),
# ) -> ModelClass:
#     """
#     Create a new item.

#     Args:
#         in_obj (ModelCreateClass): object to be created.
#         db (Session): database session.
#         _ (models.User): Current active user.

#     Returns:
#         ModelClass: Created object.

#     Raises:
#         HTTPException: if object already exists.
#     """
#     try:
#         return await model_crud.create_video_from_url(
#             url=in_obj.url, source_id=in_obj.source_id, db=db
#         )
#     except crud.RecordAlreadyExistsError as exc:
#         raise HTTPException(status_code=status.HTTP_200_OK, detail="Video already exists") from exc


# @router.patch("/{id}", response_model=ModelReadClass)
# async def update(
#     *,
#     db: Session = Depends(deps.get_db),
#     id: str,
#     in_obj: ModelUpdateClass,
#     current_user: models.User = Depends(deps.get_current_active_user),
# ) -> ModelClass:
#     """
#     Update an item.

#     Args:
#         id (str): ID of the item to update.
#         in_obj (ModelUpdateClass): object to update.
#         db (Session): database session.
#         current_user (Any): authenticated user.

#     Returns:
#         ModelClass: Updated object.

#     Raises:
#         HTTPException: if object not found.
#     """
#     video = await model_crud.get_or_none(id=id, db=db)
#     if not video:
#         if crud.user.is_superuser(user_=current_user):
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="video not found")
#     else:
#         if crud.user.is_superuser(user_=current_user):
#             return await model_crud.update(db=db, in_obj=in_obj, id=id)

#     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


# @router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete(
#     *,
#     db: Session = Depends(deps.get_db),
#     id: str,
#     current_user: models.User = Depends(deps.get_current_active_user),
# ) -> None:
#     """
#     Delete an item.

#     Args:
#         id (str): ID of the item to delete.
#         db (Session): database session.
#         current_user (models.User): authenticated user.

#     Returns:
#         None

#     Raises:
#         HTTPException: if item not found.
#     """

#     video = await model_crud.get_or_none(id=id, db=db)
#     if not video:
#         if crud.user.is_superuser(user_=current_user):
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="video not found")
#     else:
#         if crud.user.is_superuser(user_=current_user):
#             return await model_crud.remove(id=id, db=db)

#     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
