"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class LimelightBaseIE(InfoExtractor):
    _PLAYLIST_SERVICE_URL = ...


class LimelightMediaIE(LimelightBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    _PLAYLIST_SERVICE_PATH = ...


class LimelightChannelIE(LimelightBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    _PLAYLIST_SERVICE_PATH = ...


class LimelightChannelListIE(LimelightBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    _PLAYLIST_SERVICE_PATH = ...
