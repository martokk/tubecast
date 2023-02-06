"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class VideomoreBaseIE(InfoExtractor):
    _API_BASE_URL = ...
    _VALID_URL_BASE = ...


class VideomoreIE(InfoExtractor):
    IE_NAME = ...
    _VALID_URL = ...
    _EMBED_REGEX = ...
    _TESTS = ...
    _GEO_BYPASS = ...


class VideomoreVideoIE(VideomoreBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    @classmethod
    def suitable(cls, url): # -> bool:
        ...
    


class VideomoreSeasonIE(VideomoreBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    @classmethod
    def suitable(cls, url): # -> bool:
        ...
    


