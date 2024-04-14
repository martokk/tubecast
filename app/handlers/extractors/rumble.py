# import itertools
import re
from datetime import datetime

from yt_dlp.compat import compat_HTTPError, compat_str
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.extractor.rumble import RumbleChannelIE, RumbleEmbedIE
from yt_dlp.utils import (
    ExtractorError,
    UnsupportedError,
    clean_html,
    determine_ext,
    get_element_by_class,
    int_or_none,
    parse_count,
    parse_duration,
    parse_iso8601,
    traverse_obj,
    try_get,
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
                        "format_id": "mp4-360p",
                        "height": 360,
                        "url": "https://ak2.rmbl.ws/s8/2/5/M/z/1/5Mz1a.baa.1.mp4",
                        "tbr": 631,
                        "protocol": "https",
                        "video_ext": "mp4",
                        "audio_ext": "none",
                        "vbr": None,
                        "abr": None,
                    },
                    {
                        "ext": "webm",
                        "format_id": "webm-480p",
                        "height": 480,
                        "url": "https://ak2.rmbl.ws/s8/2/5/M/z/1/5Mz1a.daa.1.webm",
                        "tbr": 809,
                        "protocol": "https",
                        "video_ext": "webm",
                        "audio_ext": "none",
                        "vbr": None,
                        "abr": None,
                    },
                    {
                        "ext": "mp4",
                        "format_id": "mp4-480p",
                        "height": 480,
                        "url": "https://ak2.rmbl.ws/s8/2/5/M/z/1/5Mz1a.caa.2.mp4",
                        "tbr": 810,
                        "protocol": "https",
                        "video_ext": "mp4",
                        "audio_ext": "none",
                        "vbr": None,
                        "abr": None,
                    },
                    {
                        "ext": "mp4",
                        "format_id": "mp4-720p",
                        "height": 720,
                        "url": "https://ak2.rmbl.ws/s8/2/5/M/z/1/5Mz1a.gaa.1.mp4",
                        "tbr": 1957,
                        "protocol": "https",
                        "video_ext": "mp4",
                        "audio_ext": "none",
                        "vbr": None,
                        "abr": None,
                    },
                ],
                "subtitles": {},
                "thumbnails": [
                    {
                        "url": "https://ak2.rmbl.ws/s8/1/5/M/z/1/5Mz1a.qR4e-small-WMAR-2-News-Latest-Headline.jpg"
                    }
                ],
                "timestamp": 1571611968,
                "channel": "WMAR",
                "channel_url": "https://rumble.com/c/WMAR",
                "duration": 234,
                "uploader": "WMAR",
                "live_status": "not_live",
                "awaiting_transcoding": False,
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
        # Download webpage data
        video_id = self._match_id(url)
        # video = self._download_json(
        #     "https://rumble.com/embedJS/u3/",
        #     video_id,
        #     query={"request": "video", "ver": 2, "v": video_id},
        # )
        video = self._download_json(
            "https://rumble.com/embedJS/", video_id, query={"request": "video", "v": video_id}
        )

        # Traverse the JSON data
        sys_msg = traverse_obj(video, ("sys", "msg"))
        if sys_msg:
            self.report_warning(sys_msg, video_id=video_id)

        # Get the video formats
        formats = []
        for height, ua in (video.get("ua") or {}).items():
            for i in range(2):
                f_url = try_get(ua, lambda x: x[i], compat_str)
                if f_url:
                    ext = determine_ext(f_url)
                    f = {
                        "ext": ext,
                        "format_id": "%s-%sp" % (ext, height),
                        "height": int_or_none(height),
                        "url": f_url,
                    }
                    bitrate = try_get(ua, lambda x: x[i + 2]["bitrate"])
                    if bitrate:
                        f["tbr"] = int_or_none(bitrate)
                    formats.append(f)
        self._downloader.sort_formats({"formats": formats})

        # Live videos have a single format until Rumble transcodes other formats
        if not formats and video.get("u"):
            f_url = video["u"]
            ext = determine_ext(f_url)
            height = int_or_none(video["h"])
            formats.append(
                {
                    "ext": ext,
                    "format_id": "%s-%sp" % (ext, height),
                    "height": height,
                    "url": f_url,
                }
            )

        # Get the subtitles
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

        # Get the thumbnails
        thumbnails = traverse_obj(video, ("t", ..., {"url": "i", "width": "w", "height": "h"}))
        if not thumbnails and video.get("i"):
            thumbnails = [{"url": video["i"]}]

        # Get video data
        title = unescapeHTML(video.get("title"))
        author = video.get("author") or {}
        timestamp = parse_iso8601(video.get("pubDate"))
        channel = author.get("name")
        channel_url = author.get("url")
        uploader = author.get("name")

        # Set the live status
        if video.get("live") == 0:
            live_status = "not_live" if video.get("livestream_has_dvr") is None else "was_live"
        elif video.get("live") == 1:
            # live_status = "is_upcoming" if video.get("livestream_has_dvr") else "was_live"
            live_status = "is_upcoming" if video.get("live_placeholder") else "post_live"
        elif video.get("live") == 2:
            live_status = "is_live"
        else:
            live_status = None

        # Handle live, upcoming, and post live videos
        if live_status in {"is_live", "post_live", "is_upcoming"}:
            duration = None
            formats = []
        else:
            duration = int_or_none(video.get("duration"))

            if live_status == "was_live":
                # Handle Rumble placeholder videos for live streams
                # Rumble requires a maximum of 120 seconds for a placeholder video
                # This replaces duration and formats with null values so it will get tried on the next fetch
                dt_diff = datetime.utcnow() - datetime.fromtimestamp(timestamp)
                if (
                    dt_diff.days <= 1
                    and duration <= 121
                    and video.get("livestream_has_dvr") is True
                ):
                    duration = None
                    formats = []

        if formats and duration:
            awaiting_transcoding = False
        else:
            awaiting_transcoding = True

        return {
            "id": video_id,
            "title": title,
            "formats": formats,
            "subtitles": subtitles,
            "thumbnails": thumbnails,
            "timestamp": timestamp,
            "channel": channel,
            "channel_url": channel_url,
            "duration": duration,
            "uploader": uploader,
            "live_status": live_status,
            "awaiting_transcoding": awaiting_transcoding,
        }


class CustomRumbleChannelIE(RumbleChannelIE):
    _VALID_URL = r"(?P<url>https?://(?:www\.)?rumble\.com/(?:c|user)/(?P<id>[^&?#$/]+))"
    # _VALID_URL = r"(?P<url>https?:\/\/(?:www\.)?rumble\.com\/(?:c|user)\/(?P<id>[a-zA-Z0-9_]+))"

    _TESTS = [
        {
            "url": "https://rumble.com/c/Styxhexenhammer666",
            "playlist_mincount": 1160,
            "info_dict": {
                "url": "https://rumble.com/c/Styxhexenhammer666",
                "thumbnail": "https://ak2.rmbl.ws/z8/t/j/s/b/tjsba.baa.1-Styxhexenhammer666-qyv16v.png",
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
            "url": "https://rumble.com/user/ProjectVeritas",
            "playlist_mincount": 4,
            "info_dict": {
                "url": "https://rumble.com/user/ProjectVeritas",
                "thumbnail": "https://ak2.rmbl.ws/z0/N/U/W/w/NUWwb.asF.5-djhd3-rs1gno.jpeg",
                "description": "ProjectVeritas's Rumble Channel",
                "title": "ProjectVeritas",
                "channel": "ProjectVeritas",
                "channel_id": "ProjectVeritas",
                "channel_url": "https://rumble.com/c/ProjectVeritas",
                "uploader": "ProjectVeritas",
                "uploader_id": "ProjectVeritas",
                "uploader_url": "https://rumble.com/c/ProjectVeritas",
                "id": "ProjectVeritas",
                "_type": "playlist",
            },
        },
        {
            "url": "https://rumble.com/c/jessekelly",
            "playlist_mincount": 4,
            "info_dict": {
                "url": "https://rumble.com/c/jessekelly",
                "thumbnail": "https://ak2.rmbl.ws/z8/r/U/E/b/rUEba.baa.1-jessekelly-rxpi5t.jpeg",
                "description": "\"I'm Right\" with Jesse Kelly's Rumble Channel",
                "title": '"I\'m Right" with Jesse Kelly',
                "channel": '"I\'m Right" with Jesse Kelly',
                "channel_id": "jessekelly",
                "channel_url": "https://rumble.com/c/jessekelly",
                "uploader": '"I\'m Right" with Jesse Kelly',
                "uploader_id": "jessekelly",
                "uploader_url": "https://rumble.com/c/jessekelly",
                "id": "jessekelly",
                "_type": "playlist",
            },
        },
    ]

    def entries(self, url, playlist_id, webpage, **kwargs):
        pattern = (
            r"videostream thumbnail__grid--item.*?videostream__data--item videostream__comments"
        )
        findall = re.findall(pattern, webpage, flags=re.DOTALL)
        for video in findall:
            video_id = self._search_regex(r'data-video-id="(\d+)"', video, "video id", default=None)
            video_url = self._search_regex(
                r'href="(/[^"]+\.html)"', video, "video URL", default=None
            )
            thumbnail = self._search_regex(
                r'<img[^>]+src="([^"]+)"', video, "thumbnail", default=None
            )
            timestamp = parse_iso8601(
                self._search_regex(
                    r'<time[^>]+datetime="([^"]+)"', video, "upload datetime", default=None
                )
            )
            url = self._proto_relative_url(video_url, "https:")

            # Duration extraction
            duration_pattern = (
                r'videostream__status videostream__status--duration"\n\t\t\t>\n\t\t\t\t(.*?)\t\t\t'
            )
            duration_search = re.search(duration_pattern, video, flags=re.DOTALL)
            if duration_search:
                duration_text = duration_search.group(1).strip()
                duration = parse_duration(duration_text)
            else:
                duration = None

            # Title
            title_pattern = r"<h3[^>]*>\s*(.*?)\s*<\/h3>"
            title_search = re.search(title_pattern, video, flags=re.DOTALL)
            if title_search:
                title = title_search.group(1).strip()
                title = title.replace("\n", "").replace("\t", "").strip()
                title = title.replace("Channel: ", "")
            else:
                title = None

            # Description
            description = title

            yield {
                **kwargs,
                **self.url_result(f"https://rumble.com{video_url}"),
                "_type": "url_transparent",
                "id": video_id,
                "display_id": video_id,
                "url": f"https://rumble.com{video_url}",
                "webpage_url": f"https://rumble.com{video_url}",
                "title": title,
                "description": description,
                "thumbnail": thumbnail,
                "duration": duration,
                "timestamp": timestamp,
                "ie_key": "Rumble",  # Assuming "Rumble" extractor is defined and handles individual video pages.
            }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        #
        thumbnail_match = re.search(
            r'<img\n\t\t\t\t\t\t\t\t\tclass="channel-header--img"\n\t\t\t\t\t\t\t\t\tsrc="(.*?)"\n',
            webpage,
        )
        if not thumbnail_match:
            thumbnail_match = re.search(
                r'class="channel-header--backsplash-img"\n\t\t\t\t\t\tsrc="(.*?)"\n', webpage
            )
        thumbnail = thumbnail_match.group(1) if thumbnail_match else None

        #
        channel_match = re.search(r'channel-header--title-wrapper"><h1>(.*?)<\/h1>', webpage)
        channel = channel_match.group(1) if channel_match else None

        channel_id_match = re.search(
            r"(rel=canonical href=)(https:\/\/rumble\.com\/)(c|user)\/([^\">]+)", webpage
        )
        channel_id = channel_id_match.group(4) if channel_id_match else None

        channel_url = f"https://rumble.com/c/{channel_id}"

        #
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
            self.entries(url, playlist_id, webpage),
            playlist_id=playlist_id,
            playlist_title=f"{channel}",
            **kwargs,
        )
