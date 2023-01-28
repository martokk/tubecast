from yt_dlp import YoutubeDL

from tubecast.handlers.extractors.rumble import (
    CustomRumbleChannelIE,
    CustomRumbleEmbedIE,
    CustomRumbleIE,
)


def test_CustomRumbleChannelIE() -> None:
    with YoutubeDL() as ydl:
        ie = CustomRumbleChannelIE(ydl)

        for test_case in CustomRumbleChannelIE._TESTS:
            url = test_case["url"]
            expected_output = test_case["info_dict"]

            output = ie.extract(url)

            output.pop("entries")
            assert output == expected_output


def test_CustomRumbleEmbedIE() -> None:
    with YoutubeDL() as ydl:
        ie = CustomRumbleEmbedIE(ydl)

        for test_case in CustomRumbleEmbedIE._TESTS:
            url = test_case["url"]
            expected_output = test_case["info_dict"]

            output = ie.extract(url)

            assert output == expected_output


def test_CustomRumbleIE() -> None:
    with YoutubeDL() as ydl:
        ie = CustomRumbleIE(ydl)

        for test_case in CustomRumbleIE._TESTS:
            url = test_case["url"]
            expected_output = test_case["info_dict"]

            output = ie.extract(url)

            assert output == expected_output
