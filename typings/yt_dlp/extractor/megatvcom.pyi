"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class MegaTVComBaseIE(InfoExtractor):
    _PLAYER_DIV_ID = ...


class MegaTVComIE(MegaTVComBaseIE):
    IE_NAME = ...
    IE_DESC = ...
    _VALID_URL = ...
    _TESTS = ...


class MegaTVComEmbedIE(MegaTVComBaseIE):
    IE_NAME = ...
    IE_DESC = ...
    _VALID_URL = ...
    _EMBED_REGEX = ...
    _TESTS = ...


