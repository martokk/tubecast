"""
This type stub file was generated by pyright.
"""

from .naver import NaverBaseIE

class VLiveBaseIE(NaverBaseIE):
    _NETRC_MACHINE = ...
    _logged_in = ...


class VLiveIE(VLiveBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...


class VLivePostIE(VLiveBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...
    _FVIDEO_TMPL = ...


class VLiveChannelIE(VLiveBaseIE):
    IE_NAME = ...
    _VALID_URL = ...
    _TESTS = ...