from sqlmodel import Session

from tubecast import crud, logger, models
from tubecast.models.video import generate_video_id_from_url
from tubecast.services.videos import get_video_from_video_info_dict, get_video_info_dict

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
        return await self.create(in_obj=_video, db=db)

    async def fetch_video(self, video_id: str, db: Session) -> models.Video:
        """Fetches new data from yt-dlp for the video.

        Args:
            video_id: The ID of the video to fetch data for.
            db (Session): The database session.

        Returns:
            The updated video.
        """
        # Get the video from the database
        db_video = await self.get(id=video_id, db=db)
        source_id = db_video.source_id

        # Fetch video information from yt-dlp and create the video object
        video_info_dict = await get_video_info_dict(url=db_video.url)
        _video = await get_video_from_video_info_dict(
            video_info_dict=video_info_dict, source_id=source_id
        )

        # Update the video in the database and return it
        return await self.update(in_obj=models.VideoUpdate(**_video.dict()), id=_video.id, db=db)

    async def fetch_all_videos(self, db: Session) -> list[models.Video]:
        """
        Fetch videos from all sources.

        Args:
            db (Session): The database session.

        Returns:
            List[Video]: List of fetched videos
        """
        logger.warning("Fetching ALL Videos...")
        videos = await self.get_all(db=db) or []
        fetched = []
        for _video in videos:
            fetched.append(await self.fetch_video(video_id=_video.id, db=db))

        return fetched


video = VideoCRUD(models.Video)
