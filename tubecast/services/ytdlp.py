from typing import Any, Type

from loguru import logger
from yt_dlp import YoutubeDL
from yt_dlp.extractor.common import InfoExtractor

YDL_OPTS_BASE: dict[str, Any] = {
    "logger": logger,
    "format": "worst[ext=mp4]",
    "skip_download": True,
    "simulate": True,
    # "verbose": True,
}


async def get_info_dict(
    url: str,
    ydl_opts: dict[str, Any],
    ie_key: str | None = None,
    custom_extractors: list[Type[InfoExtractor]] | None = None,
) -> dict[str, Any]:
    """
    Use YouTube-DL to get the info dictionary for a given URL.

    Parameters:
        url (str): The URL of the object to retrieve info for.
        ydl_opts (dict[str, Any]): The options to use with YouTube-DL.
        ie_key (Optional[str]): The name of the YouTube-DL info extractor to use.
            If not provided, the default extractor will be used.
        custom_extractors (Optional[list[Type[InfoExtractor]]]): A list of
            Custom Extractors to make available to yt-dlp.

    Returns:
        dict[str, Any]: The info dictionary for the object.

    Raises:
        ValueError: If the info dictionary could not be retrieved.
    """
    with YoutubeDL(ydl_opts) as ydl:

        # Add custom_extractors
        if custom_extractors:
            for custom_extractor in custom_extractors:
                ydl.add_info_extractor(custom_extractor())

        # Get Info Dict
        info_dict: dict[str, Any] = ydl.extract_info(url, download=False, ie_key=ie_key)
        if info_dict is None:
            raise ValueError(
                f"yt-dlp did not download a info_dict object. {info_dict=} {url=} {ie_key=} {ydl_opts=}"
            )

        # Append Metadata to info_dict
        info_dict["metadata"] = {
            "url": url,
            "ydl_opts": ydl_opts,
            "ie_key": ie_key,
            "custom_extractors": custom_extractors,
        }

    return info_dict
