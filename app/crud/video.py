from sqlmodel import Session

from app import crud, logger, models
from app.models.video import generate_video_id_from_url
from app.services.video import get_video_from_video_info_dict, get_video_info_dict

from .base import BaseCRUD


class VideoCRUD(BaseCRUD[models.Video, models.VideoCreate, models.VideoUpdate]):
    async def create_video_from_url(self, url: str, source_id: str, db: Session) -> models.Video:
        """Create a new video from a URL.

        Args:
            url: The URL to create the video from.
            source_id: The id of the Source the video belongs to.
            db (Session): The database session.

        Returns:
            The created video.

        Raises:
            RecordAlreadyExistsError: If a video already exists for the given URL.
        """
        video_id = await generate_video_id_from_url(url=url)

        # Check if the video already exists
        db_video = await self.get_or_none(id=video_id, db=db)
        if db_video:
            raise crud.RecordAlreadyExistsError("Record already exists for url.")

        # Fetch video information from yt-dlp and create the video object
        video_info_dict = await get_video_info_dict(url=url)
        _video = await get_video_from_video_info_dict(
            video_info_dict=video_info_dict, source_id=source_id
        )

        # Save the video to the database
        return await self.create(obj_in=_video, db=db)


video = VideoCRUD(models.Video)
