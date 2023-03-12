from urllib.parse import ParseResult, urlparse

import shortuuid


def generate_uuid_from_url(url: str | ParseResult) -> str:
    """
    Generates a UUID from a sanitized URL, then returns the first 8 characters of the UUID.

    Args:
        url (Union[str, ParseResult]): The URL from which to generate a UUID. If a string is
            provided, it will be sanitized before generating the UUID.

    Returns:
        str: The first 8 characters of the generated UUID.
    """
    parse_result = urlparse(url) if isinstance(url, str) else url
    sanitized_url = parse_result.geturl()
    return shortuuid.uuid(sanitized_url)[:8]


def generate_uuid_from_string(string: str) -> str:
    """
    Generates a UUID from a string and returns the first 8 characters of the UUID.

    Args:
        string: String to generate the UUID from.

    Returns:
        str: First 8 characters of UUID generated.
    """
    return shortuuid.uuid(string)[:8]


def generate_uuid_random() -> str:
    """
    Generates a random UUID and returns the first 8 characters of the UUID.

    Args:
        None

    Returns:
        str: First 8 characters of UUID generated.
    """
    return shortuuid.uuid()[:8]
