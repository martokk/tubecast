"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class RCTIPlusBaseIE(InfoExtractor):
    ...


class RCTIPlusIE(RCTIPlusBaseIE):
    _VALID_URL = ...
    _TESTS = ...
    _CONVIVA_JSON_TEMPLATE = ...


class RCTIPlusSeriesIE(RCTIPlusBaseIE):
    _VALID_URL = ...
    _TESTS = ...
    _AGE_RATINGS = ...
    @classmethod
    def suitable(cls, url): # -> bool:
        ...
    


class RCTIPlusTVIE(RCTIPlusBaseIE):
    _VALID_URL = ...
    _TESTS = ...
    @classmethod
    def suitable(cls, url): # -> bool:
        ...
    

