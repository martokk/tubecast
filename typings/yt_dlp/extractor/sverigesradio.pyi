"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class SverigesRadioBaseIE(InfoExtractor):
    _BASE_URL = ...
    _QUALITIES = ...
    _EXT_TO_CODEC_MAP = ...
    _CODING_FORMAT_TO_ABR_MAP = ...


class SverigesRadioPublicationIE(SverigesRadioBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    _AUDIO_TYPE = ...


class SverigesRadioEpisodeIE(SverigesRadioBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TEST = ...
    _AUDIO_TYPE = ...

