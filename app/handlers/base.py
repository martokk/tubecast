from typing import Any, Type

from abc import abstractmethod
from urllib.parse import urlparse

from yt_dlp.extractor.common import InfoExtractor

from app.models.settings import Settings as _Settings
from app.models.source_video_link import SourceOrderBy
from app.services.ytdlp import YDL_OPTS_BASE, AwaitingTranscodingError, FormatNotFoundError

settings = _Settings()


class ServiceHandler:
    SERVICE_NAME = "Base"
    COLOR = "#333333"
    USE_PROXY = False
    REFRESH_UPDATE_INTERVAL_HOURS = 24
    REFRESH_RELEASED_RECENT_DAYS = 14
    DOMAINS: list[str] = []
    YTDLP_CUSTOM_EXTRACTORS: list[Type[InfoExtractor]] = []
    YDL_OPT_ALLOWED_EXTRACTORS: list[str] = []
    DISABLED = False

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
    async def get_source_info_dict_kwargs(self, url: str) -> dict[str, Any]:
        """


        Args:
            source_id: The ID of the source.
            url: The URL of the source.

        Returns:
            A dictionary containing the kwargs for the source info dict.
        """

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

    def get_ordered_by(self, url: str) -> str:
        return str(SourceOrderBy.RELEASED_AT.value)

    def _get_format_info_dict_from_entry_info_dict(
        self, entry_info_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Gets the format_info_dict from the entry_info_dict based of the format_id.

        Args:
            entry_info_dict: The entity dictionary returned by youtube_dl.YoutubeDL.extract_info.

        Returns:
            The dictionary from entry_info_dict['formats'] that has a 'format_id'
                value matching format_number.

        Raises:
            FormatNotFoundError: If the format_id is not found in the entry_info_dict['formats'].
            AwaitingTranscodingError: If the video is awaiting transcoding.
        """
        try:
            format_id = entry_info_dict["format_id"]
            format_info_dict: dict[str, Any] = next(
                (
                    format_dict
                    for format_dict in entry_info_dict["formats"]
                    if format_dict["format_id"] == str(format_id)
                )
            )
        except StopIteration as exc:
            raise FormatNotFoundError(
                f"Format was not found in the entry_info_dict['formats']."
            ) from exc
        except KeyError as exc:
            if entry_info_dict.get("awaiting_transcoding"):
                raise AwaitingTranscodingError("Video is awaiting transcoding.") from exc
            raise FormatNotFoundError(
                f"Could not find formats in entry_info_dict: {str(exc)}"
            ) from exc

        if "m3u8" in format_info_dict["url"]:
            raise AwaitingTranscodingError("Awaiting transcoding. 'm3u8' format not supported.")

        return format_info_dict
