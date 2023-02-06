"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class RtlNlIE(InfoExtractor):
    IE_NAME = ...
    IE_DESC = ...
    _EMBED_REGEX = ...
    _VALID_URL = ...
    _TESTS = ...


class RTLLuBaseIE(InfoExtractor):
    _MEDIA_REGEX = ...
    def get_media_url(self, webpage, video_id, media_type): # -> str | Any | tuple[str | Unknown, ...] | object | None:
        ...
    
    def get_formats_and_subtitles(self, webpage, video_id): # -> tuple[list[dict[str, str | int | Unknown | Match[str] | None]], dict[Unknown, Unknown]]:
        ...
    


class RTLLuTeleVODIE(RTLLuBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...


class RTLLuArticleIE(RTLLuBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...


class RTLLuLiveIE(RTLLuBaseIE):
    _VALID_URL = ...
    _TESTS = ...


class RTLLuRadioIE(RTLLuBaseIE):
    _VALID_URL = ...
    _TESTS = ...


