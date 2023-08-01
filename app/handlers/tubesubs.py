from typing import Any, Type

import datetime
import re

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


class TubeSubsHandler(ServiceHandler):
    SERVICE_NAME = "TubeSubs"
    COLOR = "#0083FF"
    USE_PROXY = True
    REFRESH_UPDATE_INTERVAL_HOURS = 4
    REFRESH_RELEASED_RECENT_DAYS = 14
    DOMAINS = ["tubesubs.duckdns.org"]
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
        if "playlist" not in url and "feed" not in url:
            raise InvalidSourceUrl(f"Invalid TubeSubs source URL ({str(url)})")
        return url

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
        source_id = generate_uuid_from_url(url=url)
        logo = f"/static/logos/{source_id}.png"
        ordered_by = "released_at"
        return {
            "url": url,
            "name": source_info_dict["title"],
            "author": self.SERVICE_NAME,
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
        released_at = datetime.datetime.utcfromtimestamp(entry_info_dict["timestamp"])
        url = entry_info_dict["url"].split("#")[0]
        return {
            "source_id": source_id,
            "url": url,
            "added_at": datetime.datetime.now(tz=datetime.timezone.utc),
            "title": entry_info_dict["title"],
            "description": entry_info_dict["description"],
            "duration": None,
            "thumbnail": None,
            "released_at": released_at,
            "media_url": None,
            "media_filesize": None,
        }

    def map_video_info_dict_entity_to_video_dict(
        self, entry_info_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Required by @abstractmethod of Base. Not needed for TubeSubs though.
        """
        return {}

    def get_ordered_by(self, url: str) -> str:
        return str(SourceOrderBy.CREATED_AT.value)
