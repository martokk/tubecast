from typing import Any

import datetime

from loguru import logger as _logger

from tubecast.handlers.extractors.rumble import (
    CustomRumbleChannelIE,
    CustomRumbleEmbedIE,
    CustomRumbleIE,
)
from tubecast.paths import LOG_FILE as _LOG_FILE
from tubecast.paths import TEMP_LOG_FILE as _TEMP_LOG_FILE
from tubecast.services.ytdlp import YDL_OPTS_BASE

from .base import ServiceHandler

# Main Logger
logger = _logger.bind(name="logger")
logger.add(_LOG_FILE, level="WARNING", rotation="10 MB")

temp_logger = _logger.bind(name="logger")  # TODO: This is temporary. Remove this.
temp_logger.add(_TEMP_LOG_FILE, level="CRITICAL", rotation="10 MB")


class RumbleHandler(ServiceHandler):
    USE_PROXY = False
    MAX_VIDEO_AGE_HOURS = 8
    DOMAINS = ["rumble.com"]
    YTDLP_CUSTOM_EXTRACTORS = [CustomRumbleIE, CustomRumbleChannelIE, CustomRumbleEmbedIE]
    YDL_OPT_ALLOWED_EXTRACTORS = ["CustomRumbleIE", "CustomRumbleEmbed", "CustomRumbleChannel"]

    # def sanitize_video_url(self, url: str) -> str: # TODO: Do this for rumble
    #     """
    #     Sanitizes the url to a standard format

    #     Args:
    #         url: The URL to be sanitized

    #     Returns:
    #         The sanitized URL.
    #     """
    #     url = await self.force_watch_v_format(url=url)
    #     return await super().sanitize_video_url(url=url)

    # def force_watch_v_format(self, url: str) -> str:
    #     """
    #     Extracts the YouTube video ID from a URL and returns the URL
    #     formatted like `https://www.youtube.com/watch?v=VIDEO_ID`.

    #     Args:
    #         url: The URL of the YouTube video.

    #     Returns:
    #         The formatted URL.

    #     Raises:
    #         ValueError: If the URL is not a valid YouTube video URL.
    #     """
    #     match = re.search(r"(?<=shorts/).*", url)
    #     if match:
    #         video_id = match.group()
    #     else:
    #         match = re.search(r"(?<=watch\?v=).*", url)
    #         if match:
    #             video_id = match.group()
    #         else:
    #             raise ValueError("Invalid YouTube video URL")

    #     return f"https://www.youtube.com/watch?v={video_id}"

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
        return {
            **YDL_OPTS_BASE,
            "playlistreverse": True,
            "extract_flat": extract_flat,
            "playlistend": playlistend,
            "dateafter": dateafter,
            "allowed_extractors": self.YDL_OPT_ALLOWED_EXTRACTORS,
        }

    def get_video_ydl_opts(self) -> dict[str, Any]:
        """
        Get the yt-dlp options for a video.

        Returns:
            dict: The yt-dlp options for the source.
        """
        return {
            **YDL_OPTS_BASE,
            "allowed_extractors": self.YDL_OPT_ALLOWED_EXTRACTORS,
        }

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
        return {
            "url": source_info_dict["url"],
            "name": source_info_dict["title"],
            "author": source_info_dict["uploader"],
            "logo": source_info_dict["thumbnail"],
            "ordered_by": "release",
            "description": f"{source_info_dict.get('description', source_info_dict['uploader'])}",
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
        url = entry_info_dict.get("webpage_url", entry_info_dict["url"])
        released_at = datetime.datetime.utcfromtimestamp(entry_info_dict["timestamp"])
        return {
            "source_id": source_id,
            "url": url,
            "added_at": datetime.datetime.now(tz=datetime.timezone.utc),
            "title": entry_info_dict["title"],
            "description": entry_info_dict["description"],
            "duration": entry_info_dict["duration"],
            "thumbnail": entry_info_dict["thumbnail"],
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
        format_info_dict = self._get_format_info_dict_from_entry_info_dict(
            entry_info_dict=entry_info_dict, format_number=entry_info_dict["format_id"]
        )
        media_filesize = (
            format_info_dict.get("filesize") or format_info_dict.get("filesize_approx") or 0
        )

        media_url = format_info_dict.get("url")
        released_at = datetime.datetime.utcfromtimestamp(entry_info_dict["timestamp"])

        # TODO: Finalize this solution after some time/testings to see why this happens
        # Handle when media_filesize in below 2MB
        if "live" in entry_info_dict["title"].lower():  # TODO: This is temporary. Remove
            logger.critical(
                f"'Live' found in title. The first appearance is the one causing issues."
            )
            logger.critical(
                f"\n{entry_info_dict['title']=}\n{media_filesize=}\n{media_url=}\n\n{entry_info_dict=}\n\n-----------------\n\n"
            )
        if (
            media_filesize > 0  # 0 bytes
            and media_filesize < 2 * 1024 * 1024  # 2MB
            and entry_info_dict["duration"] > 300  # 5 minutes
        ):
            logger.warning(
                f"Video '{entry_info_dict['title']}' has a filesize of {media_filesize} bytes. Setting media_url to None. {entry_info_dict=}"
            )
            media_filesize = 0
            media_url = None

        return {
            "title": entry_info_dict["title"],
            "uploader": entry_info_dict["uploader"],
            "uploader_id": entry_info_dict["channel"],
            "description": entry_info_dict.get(
                "description", f"Rumble video uploaded by {entry_info_dict['uploader']}"
            ),
            "duration": entry_info_dict["duration"],
            "url": entry_info_dict["original_url"],
            "media_url": media_url,
            "media_filesize": media_filesize,
            "thumbnail": entry_info_dict["thumbnail"],
            "released_at": released_at,
        }

    def _get_format_info_dict_from_entry_info_dict(
        self, entry_info_dict: dict[str, Any], format_number: int | str
    ) -> dict[str, Any]:
        """
        Returns the dictionary from entry_info_dict['formats'] that has a 'format_id' value
        matching format_number.

        Args:
            entry_info_dict: The entity dictionary returned by youtube_dl.YoutubeDL.extract_info.
            format_number: The 'format_id' value to search for in entry_info_dict['formats'].

        Returns:
            The dictionary from entry_info_dict['formats'] that has a 'format_id'
                value matching format_number.

        Raises:
            ValueError: If no dictionary in entry_info_dict['formats'] has a 'format_id'
                value matching format_number.
        """
        try:
            return next(
                (
                    format_dict
                    for format_dict in entry_info_dict["formats"]
                    if format_dict["format_id"] == str(format_number)
                )
            )
        except StopIteration as exc:
            raise ValueError(
                f"Format '{str(format_number)}' was not found in the entry_info_dict['formats']."
            ) from exc
