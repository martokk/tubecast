"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class ZingMp3BaseIE(InfoExtractor):
    _VALID_URL_TMPL = ...
    _GEO_COUNTRIES = ...
    _DOMAIN = ...
    _PER_PAGE = ...
    _API_SLUGS = ...


class ZingMp3IE(ZingMp3BaseIE):
    _VALID_URL = ...
    IE_NAME = ...
    IE_DESC = ...
    _TESTS = ...


class ZingMp3AlbumIE(ZingMp3BaseIE):
    _VALID_URL = ...
    _TESTS = ...
    IE_NAME = ...


class ZingMp3ChartHomeIE(ZingMp3BaseIE):
    _VALID_URL = ...
    _TESTS = ...
    IE_NAME = ...


class ZingMp3WeekChartIE(ZingMp3BaseIE):
    _VALID_URL = ...
    IE_NAME = ...
    _TESTS = ...


class ZingMp3ChartMusicVideoIE(ZingMp3BaseIE):
    _VALID_URL = ...
    IE_NAME = ...
    _TESTS = ...


class ZingMp3UserIE(ZingMp3BaseIE):
    _VALID_URL = ...
    IE_NAME = ...
    _TESTS = ...
