"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor
from .fox import FOXIE

class NationalGeographicVideoIE(InfoExtractor):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...


class NationalGeographicTVIE(FOXIE):
    _VALID_URL = ...
    _TESTS = ...
    _HOME_PAGE_URL = ...
    _API_KEY = ...
