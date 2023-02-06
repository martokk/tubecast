"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class IwaraBaseIE(InfoExtractor):
    _BASE_REGEX = ...


class IwaraIE(IwaraBaseIE):
    _VALID_URL = ...
    _TESTS = ...


class IwaraPlaylistIE(IwaraBaseIE):
    _VALID_URL = ...
    IE_NAME = ...
    _TESTS = ...


class IwaraUserIE(IwaraBaseIE):
    _VALID_URL = ...
    IE_NAME = ...
    _TESTS = ...


