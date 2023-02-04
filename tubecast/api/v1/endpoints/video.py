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
    if video:
        if crud.user.is_superuser(user_=current_user):
            return video

    elif crud.user.is_superuser(user_=current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
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
        skip (int): Number of videos to skip. Defaults to 0.
        limit (int): Number of videos to return. Defaults to 100.
        current_user (models.User): Current active user.

    Returns:
        list[ModelClass]: List of objects.
    """
    return (
        await model_crud.get_multi(db=db, skip=skip, limit=limit)
        if crud.user.is_superuser(user_=current_user)
        else await model_crud.get_multi(db=db, created_by=current_user.id, skip=skip, limit=limit)
    )


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
