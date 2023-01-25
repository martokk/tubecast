"""
This type stub file was generated by pyright.
"""

from .common import InfoExtractor

class PornHubBaseIE(InfoExtractor):
    _NETRC_MACHINE = ...
    _PORNHUB_HOST_RE = ...


class PornHubIE(PornHubBaseIE):
    IE_DESC = ...
    _VALID_URL = ...
    _EMBED_REGEX = ...
    _TESTS = ...


class PornHubPlaylistBaseIE(PornHubBaseIE):
    ...


class PornHubUserIE(PornHubPlaylistBaseIE):
    _VALID_URL = ...
    _TESTS = ...


class PornHubPagedPlaylistBaseIE(PornHubPlaylistBaseIE):
    ...


class PornHubPagedVideoListIE(PornHubPagedPlaylistBaseIE):
    _VALID_URL = ...
    _TESTS = ...
    @classmethod
    def suitable(cls, url): # -> bool:
        ...



class PornHubUserVideosUploadIE(PornHubPagedPlaylistBaseIE):
    _VALID_URL = ...
    _TESTS = ...


class PornHubPlaylistIE(PornHubPlaylistBaseIE):
    _VALID_URL = ...
    _TESTS = ...
