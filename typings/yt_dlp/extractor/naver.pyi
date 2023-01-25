"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class NaverBaseIE(InfoExtractor):
    _CAPTION_EXT_RE = ...


class NaverIE(NaverBaseIE):
    _VALID_URL = ...
    _GEO_BYPASS = ...
    _TESTS = ...


class NaverLiveIE(InfoExtractor):
    IE_NAME = ...
    _VALID_URL = ...
    _GEO_BYPASS = ...
    _TESTS = ...


class NaverNowIE(NaverBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _API_URL = ...
    _TESTS = ...
