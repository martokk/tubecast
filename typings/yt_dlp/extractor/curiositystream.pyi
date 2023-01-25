"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class CuriosityStreamBaseIE(InfoExtractor):
    _NETRC_MACHINE = ...
    _auth_token = ...


class CuriosityStreamIE(CuriosityStreamBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    _API_BASE_URL = ...


class CuriosityStreamCollectionBaseIE(CuriosityStreamBaseIE):
    ...


class CuriosityStreamCollectionsIE(CuriosityStreamCollectionBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _API_BASE_URL = ...
    _TESTS = ...


class CuriosityStreamSeriesIE(CuriosityStreamCollectionBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _API_BASE_URL = ...
    _TESTS = ...
