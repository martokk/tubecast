"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class MTVServicesInfoExtractor(InfoExtractor):
    _MOBILE_TEMPLATE = ...
    _LANG = ...


class MTVServicesEmbeddedIE(MTVServicesInfoExtractor):
    IE_NAME = ...
    _VALID_URL = ...
    _EMBED_REGEX = ...
    _TEST = ...


class MTVIE(MTVServicesInfoExtractor):
    IE_NAME = ...
    _VALID_URL = ...
    _FEED_URL = ...
    _TESTS = ...


class MTVJapanIE(MTVServicesInfoExtractor):
    IE_NAME = ...
    _VALID_URL = ...
    _TEST = ...
    _GEO_COUNTRIES = ...
    _FEED_URL = ...


class MTVVideoIE(MTVServicesInfoExtractor):
    IE_NAME = ...
    _VALID_URL = ...
    _FEED_URL = ...
    _TESTS = ...


class MTVDEIE(MTVServicesInfoExtractor):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    _GEO_COUNTRIES = ...
    _FEED_URL = ...


class MTVItaliaIE(MTVServicesInfoExtractor):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    _GEO_COUNTRIES = ...
    _FEED_URL = ...


class MTVItaliaProgrammaIE(MTVItaliaIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    _GEO_COUNTRIES = ...
    _FEED_URL = ...
