"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class TVPIE(InfoExtractor):
    IE_NAME = ...
    IE_DESC = ...
    _VALID_URL = ...
    _TESTS = ...


class TVPStreamIE(InfoExtractor):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    _PLAYER_BOX_RE = ...
    _BUTTON_RE = ...


class TVPEmbedIE(InfoExtractor):
    IE_NAME = ...
    IE_DESC = ...
    _GEO_BYPASS = ...
    _VALID_URL = ...
    _EMBED_REGEX = ...
    _TESTS = ...


class TVPVODBaseIE(InfoExtractor):
    _API_BASE_URL = ...


class TVPVODVideoIE(TVPVODBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...


class TVPVODSeriesIE(TVPVODBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
