import datetime
from pathlib import Path

from feedgen.feed import FeedGenerator

from app import logger, settings
from app.core.notify import notify
from app.models.source import Source
from app.paths import FEEDS_PATH


def get_published_date(
    created_at: datetime.datetime, released_at: datetime.datetime | None
) -> datetime.datetime:
    """
    Returns an estimated published date.

    Args:
        created_at: The date the video was added to the database.
        released_at: The date the video was released on YouTube.

    Returns:
        The latest date between `released_at` and `created_at`.
    """
    if not released_at:
        return created_at
    if released_at.date() == created_at.date():
        if released_at.time() == datetime.time(0, 0, 0):
            return created_at
    return released_at


class SourceFeedGenerator(FeedGenerator):
    def __init__(self, source: Source):
        """
        Initialize the SourceFeedGenerator object.

        Args:
            source: The source to retrieve data from.
        """
        super().__init__()
        self.load_extension("podcast")
        self.rss_file_path = get_rss_file_path(source_id=source.id)

        self._generate_feed(source=source)

    def _generate_feed(self, source: Source) -> None:
        """
        Generate the feed data.

        Args:
            source: The source to retrieve data from.
        """
        self.title(source.name)
        self.link(href=f"{settings.BASE_URL}{source.feed_url}", rel="self")
        self.id(source.id)
        self.author({"name": source.author})
        self.link(href=settings.BASE_URL, rel="alternate")
        self.logo(f"{source.logo}?=.jpg")
        self.subtitle("Generated by YoutubeRSS")
        self.description(source.description or f"{source.name}")
        self.pubDate(datetime.datetime.now(tz=datetime.timezone.utc))
        self.podcast.itunes_author(  # type: ignore # pylint: disable=no-member
            itunes_author=source.author
        )
        self.podcast.itunes_image(  # type: ignore # pylint: disable=no-member
            itunes_image=f"{source.logo}?=.jpg"
        )

        # Generate Feed Posts
        for video in source.videos:

            published_at = get_published_date(
                created_at=video.created_at, released_at=video.released_at
            )

            # Set Post
            post = self.add_entry()
            post.author({"name": video.uploader})
            post.id(video.id)
            post.title(video.title)
            post.link(href=video.url)
            post.description(video.description or " ")
            post.enclosure(
                url=f"{settings.BASE_URL}{video.feed_media_url}",
                length=str(video.media_filesize),
                type="video/mp4",
            )  # TODO: Handle non-mp4 files as well
            post.published(published_at.replace(tzinfo=datetime.timezone.utc))
            post.podcast.itunes_duration(  # type: ignore # pylint: disable=no-member
                itunes_duration=video.duration
            )
            post.podcast.itunes_image(  # type: ignore # pylint: disable=no-member
                itunes_image=f"{video.thumbnail}?=.jpg"
            )  # type: ignore # pylint: disable=no-member

    async def save(self) -> Path:
        """
        Saves a generated feed to file.

        Returns:
            The path to the saved file.
        """
        self.rss_file(filename=self.rss_file_path, encoding="UTF-8", pretty=True)
        return self.rss_file_path


# RSS File
def get_rss_file_path(source_id: str) -> Path:
    """
    Returns the file path for a 'source_id' rss file.

    Args:
        source_id: The source id to retrieve the file path for.

    Returns:
        The path to the rss file.
    """
    return FEEDS_PATH / f"{source_id}.rss"


async def get_rss_file(source_id: str) -> Path:
    """
    Returns a validated rss file.

    Args:
        source_id: The source id to retrieve the file path for.

    Returns:
        The path to the rss file.

    Raises:
        FileNotFoundError: If the rss file does not exist.
    """
    rss_file = get_rss_file_path(source_id=source_id)

    # Validate RSS File exists
    if not rss_file.exists():
        err_msg = f"RSS file ({source_id}.rss) does not exist for ({source_id=})"
        logger.critical(err_msg)
        await notify(telegram=True, email=False, text=err_msg)
        raise FileNotFoundError(err_msg)
    return rss_file


async def delete_rss_file(source_id: str) -> None:
    """
    Deletes a rss file.

    Args:
        source_id: The source id to delete the file for.
    """
    rss_file = get_rss_file_path(source_id=source_id)
    rss_file.unlink()


async def build_rss_file(source: Source) -> Path:
    """
    Builds a .rss file for source_id, saves it to disk.

    Args:
        source: The source to build the rss file for.

    Returns:
        The path to the rss file.
    """
    feed = SourceFeedGenerator(source=source)
    rss_file = await feed.save()
    return rss_file
