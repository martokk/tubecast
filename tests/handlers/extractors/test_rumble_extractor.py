from yt_dlp import YoutubeDL

from tubecast.handlers.extractors.rumble import (
    CustomRumbleChannelIE,
    CustomRumbleEmbedIE,
    CustomRumbleIE,
)


# Rumble
def test_CustomRumbleIE() -> None:
    with YoutubeDL() as ydl:
        ie = CustomRumbleIE(ydl)
        test_cases = CustomRumbleIE._TESTS  # type: ignore # pylint: disable=protected-access
        for test_case in test_cases:  # type: ignore # pylint: disable=protected-access
            url = test_case["url"]
            expected_output = test_case["info_dict"]

            output = ie.extract(url)

            assert output == expected_output


# Embed
def test_CustomRumbleEmbedIE() -> None:
    with YoutubeDL() as ydl:
        ie = CustomRumbleEmbedIE(ydl)
        test_cases = CustomRumbleEmbedIE._TESTS  # type: ignore # pylint: disable=protected-access
        for test_case in test_cases:
            url = test_case["url"]
            expected_output = test_case["info_dict"]

            output = ie.extract(url)

            assert output == expected_output


# Channel
def test_CustomRumbleChannelIE() -> None:
    with YoutubeDL() as ydl:
        ie = CustomRumbleChannelIE(ydl)
        test_cases = CustomRumbleChannelIE._TESTS  # type: ignore # pylint: disable=protected-access
        for test_case in test_cases:  # type: ignore # pylint: disable=protected-access
            url = test_case["url"]
            expected_output = test_case["info_dict"]

            output = ie.extract(url)

            output.pop("entries")
            assert output == expected_output
