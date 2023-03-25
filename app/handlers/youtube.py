from typing import Any, Type

import datetime
import re

from yt_dlp import YoutubeDL
from yt_dlp.extractor.common import InfoExtractor

from app.core.uuid import generate_uuid_from_url
from app.models.settings import Settings as _Settings
from app.models.source_video_link import SourceOrderBy
from app.services.ytdlp import (
    YDL_OPTS_BASE,
    AwaitingTranscodingError,
    FormatNotFoundError,
    Http410Error,
    IsDeletedVideoError,
    IsPrivateVideoError,
)

from .base import ServiceHandler
from .exceptions import InvalidSourceUrl

settings = _Settings()


class YoutubeHandler(ServiceHandler):
    SERVICE_NAME = "Youtube"
    COLOR = "#CC0000"
    USE_PROXY = True
    REFRESH_UPDATE_INTERVAL_HOURS = 4
    REFRESH_RELEASED_RECENT_DAYS = 14
    DOMAINS = ["youtube.com"]
    YTDLP_CUSTOM_EXTRACTORS: list[Type[InfoExtractor]] = []
    YDL_OPT_ALLOWED_EXTRACTORS: list[str] = [".*"]
    YDL_OPT_PLAYLISTEND = 20
    YDL_OPT_DATEAFTER = "now-1y"

    def sanitize_source_url(self, url: str) -> str:
        """
        Sanitizes source urls.
        - "@channel" and "channel/" URLs to "/channel/" URLs.
        - "playlist" URLs to "/playlist" URLs.

        Args:
            url: The URL to be sanitized

        Returns:
            The sanitized URL.
        """
        url = self.force_source_format(url=url)
        return super().sanitize_source_url(url=url)

    def force_source_format(self, url: str) -> str:
        """
        Sanitizes '@channel', 'channel/', and 'playlist' source URLs.

        Args:
            url: The URL to be sanitized

        Returns:
            The sanitized URL.
        """
        url.replace("https://youtube.com", "https://www.youtube.com")
        if "@" in url:
            url = self.get_channel_url_from_channel_name_id_url(url=url)
        elif "/channel" in url:
            url = self.get_channel_url_from_channel_url(url=url)
        elif "/playlist" in url:
            url = self.get_playlist_url_from_playlist_url(url=url)
        else:
            raise InvalidSourceUrl(f"Invalid YouTube video URL ({str(url)})")
        return url

    def get_channel_url_from_channel_name_id_url(self, url: str) -> str:
        """
        Sanitizes "@channel" URLs to "/channel/" URLs.

        Args:
            url: The URL to be sanitized

        Returns:
            The sanitized URL.
        """
        match = re.search(r"(?<=\/@)[\w-]+", url)
        if not match:
            raise InvalidSourceUrl(f"Invalid YouTube video URL ({str(url)})")

        ydl_opts = {
            **YDL_OPTS_BASE,
            "playlistreverse": True,
            "extract_flat": True,
            "playlistend": 0,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info_dict: dict[str, Any] = ydl.extract_info(url, download=False)

        channel_id = info_dict["channel_id"]
        channel_url = f"https://www.youtube.com/channel/{channel_id}"
        return channel_url

    def get_channel_url_from_channel_url(self, url: str) -> str:
        """
        Sanitizes "channel/" URLs to "/channel/" URLs.

        Args:
            url: The URL to be sanitized

        Returns:
            The sanitized URL.
        """
        match = re.search(r"(?<=channel\/)[\w-]+", url)
        if not match:
            raise InvalidSourceUrl(f"Invalid YouTube video URL ({str(url)})")
        return "https://www.youtube.com/channel/" + match.group()

    def get_playlist_url_from_playlist_url(self, url: str) -> str:
        """
        Sanitizes "playlist" URLs to "/playlist?list=" URLs.

        Args:
            url: The URL to be sanitized

        Returns:
            The sanitized URL.
        """
        match = re.search(r"(?<=\/playlist\?list=)[\w-]+", url)
        if not match:
            raise InvalidSourceUrl(f"Invalid YouTube video URL ({str(url)})")
        return "https://www.youtube.com/playlist?list=" + match.group()

    def sanitize_video_url(self, url: str) -> str:
        """
        Sanitizes "/shorts" and "/watch" URLs to "/watch?v=" URL.

        Args:
            url: The URL to be sanitized

        Returns:
            The sanitized "/watch?v=" URL.
        """
        url = self.force_watch_v_format(url=url)
        return super().sanitize_video_url(url=url)

    def force_watch_v_format(self, url: str) -> str:
        """
        Extracts the YouTube video ID from a URL and returns the URL
        formatted like `https://www.youtube.com/watch?v=VIDEO_ID`.

        Args:
            url: The URL of the YouTube video.

        Returns:
            The formatted URL.

        Raises:
            ValueError: If the URL is not a valid YouTube video URL.
        """
        match = re.search(r"(?<=shorts/).*", url)
        if match:
            video_id = match.group()
        else:
            match = re.search(r"(?<=watch\?v=).*", url)
            if match:
                video_id = match.group()
            else:
                raise ValueError("Invalid YouTube video URL")

        return f"https://www.youtube.com/watch?v={video_id}"

    def get_source_ydl_opts(
        self,
        *,
        extract_flat: bool = True,
        playlistreverse: bool = True,
        playlistend: int = 0,
        dateafter: str = "now-20y",
    ) -> dict[str, Any]:
        """
        Get the yt-dlp options for a source.

        Parameters:
            extract_flat (bool): Whether to extract a flat list of videos in the playlist.
            playlistreverse (bool): Whether to reverse the playlist.
            playlistend (int): The index of the last video to extract.
            dateafter (str): The date after which videos should be extracted.

        Returns:
            dict: The yt-dlp options for the source.
        """
        return {
            **YDL_OPTS_BASE,
            "playlistreverse": playlistreverse,
            "extract_flat": extract_flat,
            "playlistend": playlistend,
            "dateafter": dateafter,
            "allowed_extractors": self.YDL_OPT_ALLOWED_EXTRACTORS,
        }

    async def get_source_info_dict_kwargs(self, url: str) -> dict[str, Any]:
        """
        Get the kwargs for the source info dict.

        Args:
            source_id: The ID of the source.
            url: The URL of the source.

        Returns:
            A dictionary containing the kwargs for the source info dict.
        """
        if "/channel" in url:
            return {
                "extract_flat": True,
                "playlistreverse": True,
                "playlistend": self.YDL_OPT_PLAYLISTEND,
                "dateafter": self.YDL_OPT_DATEAFTER,
            }

        if "/playlist" in url:
            return {
                "extract_flat": True,
                "playlistreverse": False,
                "playlistend": 100,
                "dateafter": "now-20y",
            }

        raise InvalidSourceUrl(f"Source info dict kwargs not found for url: ({str(url)})")

    def map_source_info_dict_to_source_dict(
        self, source_info_dict: dict[str, Any], source_videos: list[Any]
    ) -> dict[str, Any]:
        """
        Maps a 'source_info_dict' to a Source dictionary.

        Args:
            source_info_dict: A dictionary containing information about a source.
            source_videos: A list of Video objects that belong to the source.

        Returns:
            A Source object.
        """
        url = source_info_dict["metadata"]["url"]

        if "/playlist" in url:
            source_id = generate_uuid_from_url(url=url)
            logo = f"/static/logos/{source_id}.png"
            ordered_by = "created_at"
        else:
            try:
                logo = source_info_dict["thumbnails"][-2]["url"]
            except (KeyError, IndexError):
                source_id = generate_uuid_from_url(url=source_info_dict["url"])
                logo = f"/static/logos/{source_id}.png"
            ordered_by = "released_at"
        return {
            "url": url,
            "name": source_info_dict["title"],
            "author": source_info_dict["uploader"],
            "logo": logo,
            "ordered_by": ordered_by,
            "description": source_info_dict["description"],
            "videos": source_videos,
            "extractor": source_info_dict["extractor_key"],
        }

    def map_source_info_dict_entity_to_video_dict(
        self, source_id: str, entry_info_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Maps a video 'entry_info_dict' from a 'source_info_dict' (flat_extract) to a `Video` object.
        Use this when when `extract_flat=True` is used.

        Args:
            source_id: The id of the source the video belongs to.
            entry_info_dict: A dictionary containing information about the video.

        Returns:
            A `Video` dictionary created from the `entry_info_dict`.
        """
        released_at = (
            datetime.datetime.strptime(entry_info_dict["upload_date"], "%Y%m%d").replace(
                tzinfo=datetime.timezone.utc
            )
            if entry_info_dict.get("upload_date")
            else None
        )
        url = entry_info_dict.get("webpage_url", entry_info_dict["url"])
        return {
            "source_id": source_id,
            "url": url,
            "added_at": datetime.datetime.now(tz=datetime.timezone.utc),
            "title": entry_info_dict["title"],
            "description": entry_info_dict["description"],
            "duration": entry_info_dict["duration"],
            "thumbnail": entry_info_dict.get("thumbnail"),
            "released_at": released_at,
            "media_url": None,
            "media_filesize": None,
        }

    def map_video_info_dict_entity_to_video_dict(
        self, entry_info_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Maps a video 'entry_info_dict' from a 'video_info_dict' to a `Video` object.

        Args:
            entry_info_dict: A dictionary containing information about the video.

        Returns:
            A `Video` dictionary created from the `entry_info_dict`.
        """

        # Get formatting
        try:
            format_info_dict = self._get_format_info_dict_from_entry_info_dict(
                entry_info_dict=entry_info_dict
            )
        except (FormatNotFoundError, AwaitingTranscodingError):
            format_info_dict = {}

        # Handle Private/Deleted videos
        if (
            not entry_info_dict.get("formats")
            and not entry_info_dict.get("uploader")
            and not entry_info_dict.get("release_timestamp")
            and not entry_info_dict.get("upload_date")
        ):
            raise Http410Error("Youtube video has been deleted.")

        if entry_info_dict["title"] == "[Private video]":
            raise IsPrivateVideoError("Youtube video is private.")

        if entry_info_dict["title"] == "[Deleted video]":
            raise IsDeletedVideoError("Youtube video has been deleted.")

        # Get metadata
        media_filesize = format_info_dict.get("filesize") or format_info_dict.get(
            "filesize_approx", 0
        )
        media_url = format_info_dict.get("url")
        released_at = datetime.datetime.strptime(entry_info_dict["upload_date"], "%Y%m%d").replace(
            tzinfo=datetime.timezone.utc
        )

        return {
            "title": entry_info_dict["title"],
            "uploader": entry_info_dict["uploader"],
            "uploader_id": entry_info_dict["uploader_id"],
            "description": entry_info_dict["description"],
            "duration": entry_info_dict["duration"],
            "url": entry_info_dict["webpage_url"],
            "media_url": media_url,
            "media_filesize": media_filesize,
            "thumbnail": entry_info_dict["thumbnail"],
            "released_at": released_at,
        }

    def get_ordered_by(self, url: str) -> str:
        if "/playlist" in url:
            return str(SourceOrderBy.CREATED_AT.value)
        return str(SourceOrderBy.RELEASED_AT.value)
