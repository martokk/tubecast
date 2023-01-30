"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class VoicyBaseIE(InfoExtractor):
    ...


class VoicyIE(VoicyBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    ARTICLE_LIST_API_URL = ...
    _TESTS = ...


class VoicyChannelIE(VoicyBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    PROGRAM_LIST_API_URL = ...
    _TESTS = ...
    @classmethod
    def suitable(cls, url): # -> bool:
        ...