# import itertools
import re

from yt_dlp.compat import compat_HTTPError
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.extractor.rumble import RumbleChannelIE, RumbleEmbedIE
from yt_dlp.utils import (
    ExtractorError,
    UnsupportedError,
    clean_html,
    get_element_by_class,
    int_or_none,
    parse_count,
    parse_duration,
    parse_iso8601,
    traverse_obj,
    unescapeHTML,
)


class CustomRumbleIE(InfoExtractor):
    _VALID_URL = r"https?://(?:www\.)?rumble\.com/(?P<id>v(?!ideos)[\w.-]+)[^/]*$"
    _EMBED_REGEX = [r"<a class=video-item--a href=(?P<url>/v[\w.-]+\.html)>"]
    _TESTS = [
        {
            "add_ie": ["CustomRumbleEmbed"],
            "url": "https://rumble.com/vdmum1-moose-the-dog-helps-girls-dig-a-snow-fort.html",
            "md5": "53af34098a7f92c4e51cf0bd1c33f009",
            "info_dict": {
                "ie_key": "CustomRumbleEmbed",
                "view_count": None,
                "release_timestamp": None,
                "like_count": None,
                "description": "Moose the dog is more than happy to help with digging out this epic snow fort. Great job, Moose!",
                "_type": "url_transparent",
                "url": "https://rumble.com/embed/vb0ofn",
            },
        },
    ]

    _WEBPAGE_TESTS = [
        {
            "url": "https://rumble.com/videos?page=2",
            "playlist_count": 25,
            "info_dict": {
                "id": "videos?page=2",
                "title": "All videos",
                "description": "Browse videos uploaded to Rumble.com",
                "age_limit": 0,
            },
        },
        {
            "url": "https://rumble.com/live-videos",
            "playlist_mincount": 19,
            "info_dict": {
                "id": "live-videos",
                "title": "Live Videos",
                "description": "Live videos on Rumble.com",
                "age_limit": 0,
            },
        },
        {
            "url": "https://rumble.com/search/video?q=rumble&sort=views",
            "playlist_count": 24,
            "info_dict": {
                "id": "video?q=rumble&sort=views",
                "title": "Search results for: rumble",
                "age_limit": 0,
            },
        },
    ]

    def _real_extract(self, url):  # pragma: no cover
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)
        url_info = next(
            CustomRumbleEmbedIE.extract_from_webpage(self._downloader, url, webpage), None
        )
        if not url_info:
            raise UnsupportedError(url)

        release_ts_str = self._search_regex(
            r'(?:Livestream begins|Streamed on):\s+<time datetime="([^"]+)',
            webpage,
            "release date",
            fatal=False,
            default=None,
        )
        view_count_str = self._search_regex(
            r'<span class="media-heading-info">([\d,]+) Views',
            webpage,
            "view count",
            fatal=False,
            default=None,
        )

        return self.url_result(
            url_info["url"],
            ie_key=url_info["ie_key"],
            url_transparent=True,
            view_count=parse_count(view_count_str),
            release_timestamp=parse_iso8601(release_ts_str),
            like_count=parse_count(get_element_by_class("rumbles-count", webpage)),
            description=clean_html(get_element_by_class("media-description", webpage)),
        )


class CustomRumbleEmbedIE(RumbleEmbedIE):
    _VALID_URL = r"https?:\/\/(?:www\.)?rumble\.com\/embed\/(?:[0-9a-z]+\.)?(?P<id>[0-9a-z]+)"
    # _VALID_URL = r"https?:\/\/(?:www\.)?rumble\.com\/(?:embed\/)?(?P<id>[0-9a-z]+)(?:-[^\/]*)?"
    _EMBED_REGEX = [
        rf'(?:<(?:script|iframe)[^>]+\bsrc=|["\']embedUrl["\']\s*:\s*)["\'](?P<url>{_VALID_URL})'
    ]
    _TESTS = [
        {
            "url": "https://rumble.com/embed/v5pv5f",
            "md5": "36a18a049856720189f30977ccbb2c34",
            "info_dict": {
                "id": "v5pv5f",
                "title": "WMAR 2 News Latest Headlines | October 20, 6pm",
                "formats": [
                    {
                        "ext": "mp4",
                        "url": "https://sp.rmbl.ws/s8/2/5/M/z/1/5Mz1a.baa.1.mp4",
                        "format_id": "mp4-360p",
                        "height": 360,
                        "fps": 29.97,
                        "tbr": 631,
                        "filesize": 18488017,
                        "width": 640,
                        "protocol": "https",
                        "video_ext": "mp4",
                        "audio_ext": "none",
                        "vbr": 631,
                        "abr": 0,
                    },
                    {
                        "ext": "webm",
                        "url": "https://sp.rmbl.ws/s8/2/5/M/z/1/5Mz1a.daa.1.webm",
                        "format_id": "webm-480p",
                        "height": 480,
                        "fps": 29.97,
                        "tbr": 809,
                        "filesize": 23682748,
                        "width": 854,
                        "protocol": "https",
                        "video_ext": "webm",
                        "audio_ext": "none",
                        "vbr": 809,
                        "abr": 0,
                    },
                    {
                        "ext": "mp4",
                        "url": "https://sp.rmbl.ws/s8/2/5/M/z/1/5Mz1a.caa.2.mp4",
                        "format_id": "mp4-480p",
                        "height": 480,
                        "fps": 29.97,
                        "tbr": 810,
                        "filesize": 23720936,
                        "width": 854,
                        "protocol": "https",
                        "video_ext": "mp4",
                        "audio_ext": "none",
                        "vbr": 810,
                        "abr": 0,
                    },
                    {
                        "ext": "mp4",
                        "url": "https://sp.rmbl.ws/s8/2/5/M/z/1/5Mz1a.gaa.1.mp4",
                        "format_id": "mp4-720p",
                        "height": 720,
                        "fps": 29.97,
                        "tbr": 1957,
                        "filesize": 57283801,
                        "width": 1280,
                        "protocol": "https",
                        "video_ext": "mp4",
                        "audio_ext": "none",
                        "vbr": 1957,
                        "abr": 0,
                    },
                ],
                "subtitles": {},
                "thumbnails": [
                    {
                        "url": "https://sp.rmbl.ws/s8/1/5/M/z/1/5Mz1a.qR4e-small-WMAR-2-News-Latest-Headline.jpg"
                    }
                ],
                "timestamp": 1571611968,
                "channel": "WMAR",
                "channel_url": "https://rumble.com/c/WMAR",
                "duration": 234,
                "uploader": "WMAR",
                "live_status": "not_live",
            },
        },
    ]

    _WEBPAGE_TESTS = [
        {
            "note": "Rumble embed",
            "url": "https://rumble.com/vdmum1-moose-the-dog-helps-girls-dig-a-snow-fort.html",
            "md5": "53af34098a7f92c4e51cf0bd1c33f009",
            "info_dict": {
                "id": "vb0ofn",
                "ext": "mp4",
                "timestamp": 1612662578,
                "uploader": "LovingMontana",
                "channel": "LovingMontana",
                "upload_date": "20210207",
                "title": "Winter-loving dog helps girls dig a snow fort ",
                "channel_url": "https://rumble.com/c/c-546523",
                "thumbnail": "https://sp.rmbl.ws/s8/1/5/f/x/x/5fxxb.OvCc.1-small-Moose-The-Dog-Helps-Girls-D.jpg",
                "duration": 103,
                "live_status": "not_live",
            },
        },
        {
            "note": "Rumble JS embed",
            "url": "https://therightscoop.com/what-does-9-plus-1-plus-1-equal-listen-to-this-audio-of-attempted-kavanaugh-assassins-call-and-youll-get-it",
            "md5": "4701209ac99095592e73dbba21889690",
            "info_dict": {
                "id": "v15eqxl",
                "ext": "mp4",
                "channel": "Mr Producer Media",
                "duration": 92,
                "title": "911 Audio From The Man Who Wanted To Kill Supreme Court Justice Kavanaugh",
                "channel_url": "https://rumble.com/c/RichSementa",
                "thumbnail": "https://sp.rmbl.ws/s8/1/P/j/f/A/PjfAe.OvCc-small-911-Audio-From-The-Man-Who-.jpg",
                "timestamp": 1654892716,
                "uploader": "Mr Producer Media",
                "upload_date": "20220610",
                "live_status": "not_live",
            },
        },
    ]

    @classmethod
    def _extract_embed_urls(cls, url, webpage):  # pragma: no cover
        embeds = tuple(super()._extract_embed_urls(url, webpage))
        if embeds:
            return embeds
        return [
            f'https://rumble.com/embed/{mobj.group("id")}'
            for mobj in re.finditer(
                r'<script>\s*Rumble\(\s*"play"\s*,\s*{\s*[\'"]video[\'"]\s*:\s*[\'"](?P<id>[0-9a-z]+)[\'"]',
                webpage,
            )
        ]

    def _real_extract(self, url):  # pragma: no cover
        video_id = self._match_id(url)
        video = self._download_json(
            "https://rumble.com/embedJS/u3/",
            video_id,
            query={"request": "video", "ver": 2, "v": video_id},
        )

        sys_msg = traverse_obj(video, ("sys", "msg"))
        if sys_msg:
            self.report_warning(sys_msg, video_id=video_id)

        if video.get("live") == 0:
            live_status = "not_live" if video.get("livestream_has_dvr") is None else "was_live"
        elif video.get("live") == 1:
            live_status = "is_upcoming" if video.get("livestream_has_dvr") else "was_live"
        elif video.get("live") == 2:
            live_status = "is_live"
        else:
            live_status = None

        formats = []
        for ext, ext_info in (video.get("ua") or {}).items():
            for height, video_info in (ext_info or {}).items():
                meta = video_info.get("meta") or {}
                if not video_info.get("url"):
                    continue
                if ext == "hls":
                    if meta.get("live") is True and video.get("live") == 1:
                        live_status = "post_live"
                    formats.extend(
                        self._extract_m3u8_formats(
                            video_info["url"],
                            video_id,
                            ext="mp4",
                            m3u8_id="hls",
                            fatal=False,
                            live=live_status == "is_live",
                        )
                    )
                    continue
                formats.append(
                    {
                        "ext": ext,
                        "url": video_info["url"],
                        "format_id": "%s-%sp" % (ext, height),
                        "height": int_or_none(height),
                        "fps": video.get("fps"),
                        **traverse_obj(
                            meta,
                            {
                                "tbr": "bitrate",
                                "filesize": "size",
                                "width": "w",
                                "height": "h",
                            },
                            default={},
                        ),
                    }
                )
        self._sort_formats(formats)

        subtitles = {
            lang: [
                {
                    "url": sub_info["path"],
                    "name": sub_info.get("language") or "",
                }
            ]
            for lang, sub_info in (video.get("cc") or {}).items()
            if sub_info.get("path")
        }

        author = video.get("author") or {}
        thumbnails = traverse_obj(video, ("t", ..., {"url": "i", "width": "w", "height": "h"}))
        if not thumbnails and video.get("i"):
            thumbnails = [{"url": video["i"]}]

        if live_status in {"is_live", "post_live"}:
            duration = None
        else:
            duration = int_or_none(video.get("duration"))

        return {
            "id": video_id,
            "title": unescapeHTML(video.get("title")),
            "formats": formats,
            "subtitles": subtitles,
            "thumbnails": thumbnails,
            "timestamp": parse_iso8601(video.get("pubDate")),
            "channel": author.get("name"),
            "channel_url": author.get("url"),
            "duration": duration,
            "uploader": author.get("name"),
            "live_status": live_status,
        }


class CustomRumbleChannelIE(RumbleChannelIE):
    _VALID_URL = r"(?P<url>https?://(?:www\.)?rumble\.com/(?:c|user)/(?P<id>[^&?#$/]+))"

    _TESTS = [
        {
            "url": "https://rumble.com/c/Styxhexenhammer666",
            "playlist_mincount": 1160,
            "info_dict": {
                "url": "https://rumble.com/c/Styxhexenhammer666",
                "thumbnail": "https://sp.rmbl.ws/z8/t/j/s/b/tjsba.baa.1-Styxhexenhammer666-qyv16v.png",
                "description": "Styxhexenhammer666's Rumble Channel",
                "title": "Styxhexenhammer666",
                "channel": "Styxhexenhammer666",
                "channel_id": "Styxhexenhammer666",
                "channel_url": "https://rumble.com/c/Styxhexenhammer666",
                "uploader": "Styxhexenhammer666",
                "uploader_id": "Styxhexenhammer666",
                "uploader_url": "https://rumble.com/c/Styxhexenhammer666",
                "id": "Styxhexenhammer666",
                "_type": "playlist",
            },
        },
        {
            "url": "https://rumble.com/user/goldenpoodleharleyeuna",
            "playlist_mincount": 4,
            "info_dict": {
                "url": "https://rumble.com/user/goldenpoodleharleyeuna",
                "thumbnail": "https://sp.rmbl.ws/z0/V/N/R/Y/VNRYc.asF-rvy7j-qzsad1.jpeg",
                "description": "goldenpoodleharleyeuna's Rumble Channel",
                "title": "goldenpoodleharleyeuna",
                "channel": "goldenpoodleharleyeuna",
                "channel_id": "goldenpoodleharleyeuna",
                "channel_url": "https://rumble.com/c/goldenpoodleharleyeuna",
                "uploader": "goldenpoodleharleyeuna",
                "uploader_id": "goldenpoodleharleyeuna",
                "uploader_url": "https://rumble.com/c/goldenpoodleharleyeuna",
                "id": "goldenpoodleharleyeuna",
                "_type": "playlist",
            },
        },
    ]

    def entries(self, url, playlist_id, webpage, **kwargs):  # pragma: no cover
        try:
            webpage = self._download_webpage(
                f"{url}?page=1", playlist_id, note="Downloading page 1"
            )
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 404:
                return
            raise

        for container in re.findall(
            r'<li class="video-listing-entry">(.+?)</li>', webpage, flags=re.DOTALL
        ):
            # Handle if video is a LIVE video.
            live_match = re.search(r'class=video-item--live data-value="([^"]+)', container)
            if live_match:
                if live_match.group(1) == "LIVE":
                    continue

            # Build Entry
            yield self._build_entry(container=container, **kwargs)

    def _build_entry(self, container, **kwargs):  # pragma: no cover
        # Scrape Remaining Data
        video_id_match = re.search(r"\/(v[^-]*)-", container)
        video_id = video_id_match.group(1) if video_id_match else None

        video_url_match = re.search(r"class=video-item--a\s?href=([^>]+\.html)", container)
        video_url = video_url_match.group(1) if video_url_match else None

        # title = re.search(r'title="([^\"]+)"', container).group(1)'
        title_match = re.search(r"class=video-item--title>([^\<]+)<\/h3>", container)
        title = title_match.group(1) if title_match else None

        # description = re.search(r'<p class="description"\s*>(.+?)</p>', container).group(1)

        timestamp_match = re.search(r'datetime=([^\s">]+)', container)
        timestamp = parse_iso8601(timestamp_match.group(1)) if timestamp_match else None

        thumbnail_match = re.search(r"src=([^\s>]+)", container)
        thumbnail = thumbnail_match.group(1) if thumbnail_match else None

        duration_match = re.search(r"class=video-item--duration data-value=([^\">]+)>", container)
        duration = parse_duration(duration_match.group(1)) if duration_match else None

        return {
            **kwargs,
            **self.url_result(f"https://rumble.com{video_url}"),
            "id": video_id,
            "display_id": video_id,
            "title": title,
            "description": None,
            "timestamp": timestamp,
            "thumbnail": thumbnail,
            "duration": duration,
        }

    def _real_extract(self, url):
        url, playlist_id = self._match_valid_url(url).groups()
        webpage = self._download_webpage(
            f"{url}?page=1", note="Downloading webpage", video_id=playlist_id
        )

        thumbnail_match = re.search(r"class=listing-header--thumb src=([^\s>]+)", webpage)
        thumbnail = thumbnail_match.group(1) if thumbnail_match else None

        channel_match = re.search(r"class=ellipsis-1>([^\">]+)<", webpage)
        channel = channel_match.group(1) if channel_match else None

        channel_id_match = re.search(
            r"(rel=canonical href=)(https:\/\/rumble\.com\/)(c|user)\/([^\">]+)", webpage
        )
        channel_id = channel_id_match.group(4) if channel_id_match else None

        channel_url = f"https://rumble.com/c/{channel_id}"
        uploader = channel
        uploader_id = channel_id
        uploader_url = channel_url
        kwargs = {
            "url": url,
            "thumbnail": thumbnail,
            "description": f"{channel}'s Rumble Channel",
            "title": channel,
            "channel": channel,
            "channel_id": channel_id,
            "channel_url": channel_url,
            "uploader": uploader,
            "uploader_id": uploader_id,
            "uploader_url": uploader_url,
        }
        return self.playlist_result(
            self.entries(url, playlist_id, webpage=webpage), playlist_id=playlist_id, **kwargs
        )
