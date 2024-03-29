import datetime
from pathlib import Path

from feedgen.feed import FeedGenerator

from app import settings
from app.models import Filter, Source
from app.models.source_video_link import SourceOrderBy
from app.paths import FEEDS_PATH


def get_published_at(
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
    def __init__(self, source: Source | None = None, filter: Filter | None = None):
        """
        Initialize the SourceFeedGenerator object.

        Args:
            source: The source to retrieve data from.
            filter: The filter to retrieve data from.
        """
        super().__init__()
        self.load_extension("podcast")

        if source:
            self.rss_file_path = get_rss_file_path(id=source.id)
            self._generate_feed(source=source)
        elif filter:
            self.rss_file_path = get_rss_file_path(id=filter.id)
            self._generate_feed(filter=filter)
        else:
            raise ValueError("Either source or filter must be provided")

    def _generate_feed(self, source: Source | None = None, filter: Filter | None = None) -> None:
        """
        Generate the feed data.

        Args:
            source: The source to retrieve data from.
            filter: The filter to retrieve data from.
        """
        if filter:
            id = filter.id
            source = filter.source
            title = f"{source.name} - [{filter.name}]"
            link = f"{settings.BASE_URL}{filter.feed_url}"
            videos = filter.videos()
            ordered_by = filter.ordered_by

        elif source:
            id = source.id
            title = source.name
            link = f"{settings.BASE_URL}{source.feed_url}"
            videos = source.videos
            ordered_by = source.ordered_by

        else:
            raise ValueError("Either source or filter must be provided")  # pragma: no cover

        source_logo = source.logo if "http" in source.logo else f"{settings.BASE_URL}{source.logo}"

        # Filter/Source Unique Data
        self.title(title)
        self.link(href=link, rel="self")
        self.id(id)

        # Shared Data
        self.author({"name": source.author})
        self.link(href=settings.BASE_URL, rel="alternate")
        self.logo(f"{source_logo}?=.jpg")
        self.subtitle(f"Generated by {settings.PROJECT_NAME}")
        self.description(source.description or f"{source.name}")
        self.pubDate(datetime.datetime.now(tz=datetime.timezone.utc))
        self.podcast.itunes_author(  # type: ignore # pylint: disable=no-member
            itunes_author=source.author
        )
        self.podcast.itunes_image(  # type: ignore # pylint: disable=no-member
            itunes_image=f"{source_logo}?=.jpg"
        )

        # Generate Feed Posts
        for video in videos:
            # Get Published Date
            if ordered_by == SourceOrderBy.CREATED_AT.value:
                published_at = video.created_at  # pragma: no cover
            else:
                published_at = get_published_at(
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
                length=str(video.media_filesize or 1),
                type="video/mp4",
            )  # TODO: Handle non-mp4 files as well
            post.published(published_at.replace(tzinfo=datetime.timezone.utc))
            post.podcast.itunes_duration(  # type: ignore # pylint: disable=no-member
                itunes_duration=video.duration
            )
            if video.thumbnail:
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
def get_rss_file_path(id: str) -> Path:
    """
    Returns the file path for a rss file.

    Args:
        id: The source/filter id to retrieve the file path for.

    Returns:
        The path to the rss file.
    """
    return FEEDS_PATH / f"{id}.rss"


async def get_rss_file(id: str) -> Path:
    """
    Returns a validated rss file.

    Args:
        id: The source/filter id to retrieve the file path for.

    Returns:
        The path to the rss file.

    Raises:
        FileNotFoundError: If the rss file does not exist.
    """
    rss_file = get_rss_file_path(id=id)

    # Validate RSS File exists
    if not rss_file.exists():
        raise FileNotFoundError()
    return rss_file


async def delete_rss_file(id: str) -> None:
    """
    Deletes a rss file.

    Args:
        id: The source/filter id to delete the file for.
    """
    rss_file = get_rss_file_path(id=id)
    rss_file.unlink()


async def build_rss_file(source: Source | None = None, filter: Filter | None = None) -> Path:
    """
    Builds a .rss file, saves it to disk.

    Args:
        source: The source to build the rss file for.
        filter: The filter to build the rss file for.

    Returns:
        The path to the rss file.
    """
    feed = SourceFeedGenerator(source=source, filter=filter)
    rss_file = await feed.save()
    return rss_file


async def build_source_rss_files(source: Source) -> None:
    await build_rss_file(source=source)
    for filter in source.filters:
        await build_rss_file(filter=filter)
