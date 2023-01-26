from typing import Any

MOCKED_SOURCE_1 = {
    "id": "7hyhcvzT",
    "url": "https://rumble.com/c/Styxhexenhammer666",
    "name": "Styxhexenhammer666",
    "logo": "https://sp.rmbl.ws/z8/t/j/s/b/tjsba.baa.1-Styxhexenhammer666-qyv16v.png",
    "ordered_by": "release",
    "feed_url": "/feed/7hyhcvzT",
    "handler": "RumbleHandler",
    "author": "Styxhexenhammer666",
    "description": "Styxhexenhammer666's Rumble Channel",
    "extractor": "CustomRumbleChannel",
    "created_by": "ZbFPeSXW",
}

MOCKED_SOURCE_2 = {
    "id": "mLC5c5NH",
    "url": "https://rumble.com/c/KimIversen",
    "name": "Kim Iversen",
    "author": "Kim Iversen",
    "logo": "https://sp.rmbl.ws/z8/k/N/n/f/kNnfa.baa-KimIversen-r6nek8.png",
    "description": "Kim Iversen's Rumble Channel",
    "ordered_by": "release",
    "feed_url": "/feed/mLC5c5NH",
    "extractor": "CustomRumbleChannel",
    "handler": "RumbleHandler",
    "created_by": "ZbFPeSXW",
}

MOCKED_SOURCES = [MOCKED_SOURCE_1, MOCKED_SOURCE_2]


MOCKED_SOURCE_INFO_DICT = {
    "url": MOCKED_SOURCE_1["url"],
    "entries": [],
    "title": MOCKED_SOURCE_1["name"],
    "uploader": MOCKED_SOURCE_1["author"],
    "thumbnail": MOCKED_SOURCE_1["logo"],
    "description": MOCKED_SOURCE_1["description"],
    "extractor_key": MOCKED_SOURCE_1["extractor"],
}


def get_mocked_source_info_dict(*args: Any, **kwargs: Any) -> dict[str, Any]:
    url = args[1]
    for mocked_source in MOCKED_SOURCES:
        if mocked_source["url"] == url:
            return {
                "url": mocked_source["url"],
                "entries": [],
                "title": mocked_source["name"],
                "uploader": mocked_source["author"],
                "thumbnail": mocked_source["logo"],
                "description": mocked_source["description"],
                "extractor_key": mocked_source["extractor"],
            }
    raise Exception(f"Mocked source not found for url: {url}")
