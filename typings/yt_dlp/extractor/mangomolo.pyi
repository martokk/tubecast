"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class MangomoloBaseIE(InfoExtractor):
    _BASE_REGEX = ...
    _SLUG = ...


class MangomoloVideoIE(MangomoloBaseIE):
    _TYPE = ...
    IE_NAME = ...
    _SLUG = ...
    _IS_LIVE = ...


class MangomoloLiveIE(MangomoloBaseIE):
    _TYPE = ...
    IE_NAME = ...
    _SLUG = ...
    _IS_LIVE = ...
