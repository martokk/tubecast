"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class HitboxIE(InfoExtractor):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...


class HitboxLiveIE(HitboxIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    @classmethod
    def suitable(cls, url): # -> bool:
        ...
