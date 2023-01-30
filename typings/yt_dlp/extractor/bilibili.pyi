"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor, SearchInfoExtractor

class BilibiliBaseIE(InfoExtractor):
    def extract_formats(self, play_info): # -> list[dict[str, Unknown | list[Unknown] | object | str | float | int | None]]:
        ...

    def json2srt(self, json_data): # -> str:
        ...



class BiliBiliIE(BilibiliBaseIE):
    _VALID_URL = ...
    _TESTS = ...


class BiliBiliBangumiIE(BilibiliBaseIE):
    _VALID_URL = ...
    _TESTS = ...


class BiliBiliBangumiMediaIE(InfoExtractor):
    _VALID_URL = ...
    _TESTS = ...


class BilibiliSpaceBaseIE(InfoExtractor):
    ...


class BilibiliSpaceVideoIE(BilibiliSpaceBaseIE):
    _VALID_URL = ...
    _TESTS = ...


class BilibiliSpaceAudioIE(BilibiliSpaceBaseIE):
    _VALID_URL = ...
    _TESTS = ...


class BilibiliSpacePlaylistIE(BilibiliSpaceBaseIE):
    _VALID_URL = ...
    _TESTS = ...


class BilibiliCategoryIE(InfoExtractor):
    IE_NAME = ...
    _MAX_RESULTS = ...
    _VALID_URL = ...
    _TESTS = ...


class BiliBiliSearchIE(SearchInfoExtractor):
    IE_DESC = ...
    _MAX_RESULTS = ...
    _SEARCH_KEY = ...


class BilibiliAudioBaseIE(InfoExtractor):
    ...


class BilibiliAudioIE(BilibiliAudioBaseIE):
    _VALID_URL = ...
    _TEST = ...


class BilibiliAudioAlbumIE(BilibiliAudioBaseIE):
    _VALID_URL = ...
    _TEST = ...


class BiliBiliPlayerIE(InfoExtractor):
    _VALID_URL = ...
    _TEST = ...


class BiliIntlBaseIE(InfoExtractor):
    _API_URL = ...
    _NETRC_MACHINE = ...
    def json2srt(self, json): # -> str:
        ...



class BiliIntlIE(BiliIntlBaseIE):
    _VALID_URL = ...
    _TESTS = ...


class BiliIntlSeriesIE(BiliIntlBaseIE):
    _VALID_URL = ...
    _TESTS = ...


class BiliLiveIE(InfoExtractor):
    _VALID_URL = ...
    _TESTS = ...
    _FORMATS = ...
    _quality = ...