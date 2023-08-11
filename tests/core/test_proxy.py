from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException, Request

from app.core.proxy import reverse_proxy


async def test_reverse_proxy_valid_url(test_request: Request) -> None:
    url = "https://www.example.com"
    response = await reverse_proxy(url, test_request)
    assert response.status_code == 200


async def test_reverse_proxy_non_existing_url(test_request: Request) -> None:
    url = "https://www.nonexisting-example.com"
    try:
        await reverse_proxy(url, test_request)
    except httpx.ConnectError as e:
        assert (
            str(e)
            == "Could not connect to https://www.nonexisting-example.com. Invalid URL. e=ConnectError('[Errno -2] Name or service not known')"
        )


async def test_reverse_proxy_non_200_status_code(test_request: Request) -> None:
    url = "https://someurl.com/api"
    request = Request(scope={"type": "http", "method": "GET", "path": url})

    with patch("app.core.proxy.client.send") as mock:
        mock.return_value = AsyncMock(
            status_code=410,
            headers={"Content-Type": "application/json"},
            aiter_raw=AsyncMock(),
            aclose=AsyncMock(),
        )

        with pytest.raises(HTTPException) as e:
            await reverse_proxy(url, request)
        success = False
        if (e is not None) and (e.value.status_code == 410):
            success = True
        assert success == True
