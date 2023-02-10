from typing import Any, Type

from abc import abstractmethod
from urllib.parse import urlparse

from yt_dlp.extractor.common import InfoExtractor

from tubecast.services.ytdlp import YDL_OPTS_BASE


class ServiceHandler:
    SERVICE_NAME = "Base"
    USE_PROXY = False
    MAX_VIDEO_AGE_HOURS = 24
    DOMAINS: list[str] = []
    YTDLP_CUSTOM_EXTRACTORS: list[Type[InfoExtractor]] = []
    YDL_OPT_ALLOWED_EXTRACTORS: list[str] = []

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def sanitize_url(self, url: str) -> str:
        """
        Sanitizes the url to a standard format

        Args:
            url: The URL to be sanitized

        Returns:
            The sanitized URL.
        """
        parsed_url = urlparse(url)
        return parsed_url.geturl()

    def sanitize_source_url(self, url: str) -> str:
        """
        Sanitizes the Source url to a standard format

        Args:
            url: The URL to be sanitized

        Returns:
            The sanitized URL.
        """
        return self.sanitize_url(url=url)

    def sanitize_video_url(self, url: str) -> str:
        """
        Sanitizes the Source url to a standard format

        Args:
            url: The URL to be sanitized

        Returns:
            The sanitized URL.
        """
        return self.sanitize_url(url=url)

    @abstractmethod
    def get_source_ydl_opts(
        self, *, extract_flat: bool, playlistreverse: bool, playlistend: int, dateafter: str
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

    def get_video_ydl_opts(self) -> dict[str, Any]:
        """
        Get the yt-dlp options for a video.

        Returns:
            dict: The yt-dlp options for the source.
        """
        return YDL_OPTS_BASE

    @abstractmethod
    def map_source_info_dict_to_source_dict(
        self, source_info_dict: dict[str, Any], source_videos: list[Any]
    ) -> dict[str, Any]:
        """
        Maps a 'source_info_dict' to a Source dict.

        Args:
            source_info_dict: A dictionary containing information about a source.
            source_videos: A list of Video objects that belong to the source.

        Returns:
            A Source dict.
        """

    @abstractmethod
    def map_source_info_dict_entity_to_video_dict(
        self, source_id: str, entry_info_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Maps the entry_info_dict (the info_dict for the video) to a Video dict.

        Args:
            source_id: The id of the source the video belongs to.
            entry_info_dict: A dictionary containing video information from yt-dlp

        Returns:
            A Video dict created from the information in the entry_info_dict.
        """

    @abstractmethod
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
