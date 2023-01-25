"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class ARDMediathekBaseIE(InfoExtractor):
    _GEO_COUNTRIES = ...


class ARDMediathekIE(ARDMediathekBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    @classmethod
    def suitable(cls, url): # -> bool:
        ...



class ARDIE(InfoExtractor):
    _VALID_URL = ...
    _TESTS = ...


class ARDBetaMediathekIE(ARDMediathekBaseIE):
    _VALID_URL = ...
    _TESTS = ...
