"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

def md5_text(text): # -> str:
    ...

class IqiyiSDK:
    def __init__(self, target, ip, timestamp) -> None:
        ...

    @staticmethod
    def split_sum(data): # -> compat_str:
        ...

    @staticmethod
    def digit_sum(num): # -> compat_str:
        ...

    def even_odd(self): # -> tuple[compat_str, compat_str]:
        ...

    def preprocess(self, chunksize): # -> tuple[list[Unknown], list[int]]:
        ...

    def mod(self, modulus): # -> None:
        ...

    def split(self, chunksize): # -> None:
        ...

    def handle_input16(self): # -> None:
        ...

    def handle_input8(self): # -> None:
        ...

    def handleSum(self): # -> None:
        ...

    def date(self, scheme): # -> None:
        ...

    def split_time_even_odd(self): # -> None:
        ...

    def split_time_odd_even(self): # -> None:
        ...

    def split_ip_time_sum(self): # -> None:
        ...

    def split_time_ip_sum(self): # -> None:
        ...



class IqiyiSDKInterpreter:
    def __init__(self, sdk_code) -> None:
        ...

    def run(self, target, ip, timestamp): # -> str:
        ...



class IqiyiIE(InfoExtractor):
    IE_NAME = ...
    IE_DESC = ...
    _VALID_URL = ...
    _NETRC_MACHINE = ...
    _TESTS = ...
    _FORMATS_MAP = ...
    def get_raw_data(self, tvid, video_id): # -> Any:
        ...



class IqIE(InfoExtractor):
    IE_NAME = ...
    IE_DESC = ...
    _VALID_URL = ...
    _TESTS = ...
    _BID_TAGS = ...
    _LID_TAGS = ...
    _DASH_JS = ...


class IqAlbumIE(InfoExtractor):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
