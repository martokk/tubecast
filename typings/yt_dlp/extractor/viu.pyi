"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class ViuBaseIE(InfoExtractor):
    ...


class ViuIE(ViuBaseIE):
    _VALID_URL = ...
    _TESTS = ...


class ViuPlaylistIE(ViuBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TEST = ...


class ViuOTTIE(InfoExtractor):
    IE_NAME = ...
    _NETRC_MACHINE = ...
    _VALID_URL = ...
    _TESTS = ...
    _AREA_ID = ...
    _LANGUAGE_FLAG = ...
    _user_token = ...
    _auth_codes = ...
