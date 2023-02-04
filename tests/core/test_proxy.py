from fastapi import Request

from tubecast.core.proxy import reverse_proxy


async def test_reverse_proxy_valid_url(test_request: Request) -> None:
    url = "https://www.example.com"
    response = await reverse_proxy(url, test_request)
    assert response.status_code == 200


async def test_reverse_proxy_non_existing_url(test_request: Request) -> None:
    url = "https://www.nonexisting-example.com"
    try:
        await reverse_proxy(url, test_request)
    except ValueError as e:
        assert str(e) == "Invalid URL"
