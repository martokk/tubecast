import re

import httpx
from fastapi import HTTPException, status
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app import logger, settings


class Http403ForbiddenError(Exception):
    ...


async def reverse_proxy(url: str, request: Request) -> StreamingResponse:
    """
    Reverse proxy a request to a given URL.

    Args:
        url (str): URL to reverse proxy to.
        request (Request): Request to reverse proxy.

    Returns:
        StreamingResponse: Response from reverse proxy.

    Raises:
        HTTPException: If reverse proxy request fails.
    """
    client = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=100), timeout=httpx.Timeout(30.0)
    )

    rp_request = await build_reverse_proxy_request(client=client, url=url, method=request.method)
    rp_response = await send_reverse_proxy_request(client=client, rp_request=rp_request)

    # Handle 403 Forbidden status
    if rp_response.status_code == status.HTTP_403_FORBIDDEN:
        raise Http403ForbiddenError()

    # Handle if not 200 OK status
    if rp_response.status_code != status.HTTP_200_OK:
        ip_from_url = extract_ip_from_url(url=rp_response.url)
        logger.error(
            f"Reverse proxy request failed for url ('{rp_response.url}') with "
            f"status code {rp_response.status_code}. "
            f"{ip_from_url=} {settings.PROXY_HOST=} {rp_response=} {rp_request=}"
        )
        await rp_response.aclose()
        raise HTTPException(status_code=rp_response.status_code)

    # Stream Response
    return StreamingResponse(
        rp_response.aiter_raw(),
        status_code=rp_response.status_code,
        headers=rp_response.headers,
        background=BackgroundTask(rp_response.aclose),
    )


async def build_reverse_proxy_request(
    client: httpx.AsyncClient, url: str | httpx.URL, method: str
) -> httpx.Request:
    """
    Build a reverse proxy request.

    Args:
        url (str | httpx.URL): URL to build request for.
        method (str): HTTP method for the request.

    Returns:
        httpx.Request: Reverse proxy request.
    """
    _url = httpx.URL(url=url)
    return client.build_request(method=method, url=_url)


async def send_reverse_proxy_request(
    client: httpx.AsyncClient, rp_request: httpx.Request
) -> httpx.Response:
    """
    Send a reverse proxy request and handle redirects.

    Args:
        rp_request (httpx.Request): Reverse proxy request.

    Returns:
        httpx.Response: Response from reverse proxy request.
    """
    try:
        rp_response = await client.send(request=rp_request, stream=True)
    except httpx.ConnectError as e:
        error_msg = f"Could not connect to {rp_request.url}. Invalid URL. {e=}"
        logger.error(error_msg)
        raise httpx.ConnectError(error_msg) from e
    except httpx.PoolTimeout as e:
        logger.error(e)
        raise e

    # Handle 302 Found re-directs to get to final response
    while rp_response.status_code == status.HTTP_302_FOUND:
        rp_response = await follow_302_redirect(
            client=client, method=rp_request.method, rp_response=rp_response
        )

    return rp_response


async def follow_302_redirect(
    client: httpx.AsyncClient, method: str, rp_response: httpx.Response
) -> httpx.Response:
    """
    Follow a 302 redirect response to the final response.

    Args:
        method (str): HTTP method.
        rp_response (httpx.Response): Original response with 302 status.

    Returns:
        httpx.Response: Final response after following redirects.
    """
    if not rp_response.next_request:
        await rp_response.aclose()
        raise ValueError("Could not find redirect URL from response.")

    # Close existing response
    url = rp_response.next_request.url
    method = rp_response.request.method
    await rp_response.aclose()

    # Generate new response
    rp_request = await build_reverse_proxy_request(client=client, url=url, method=method)
    rp_response = await send_reverse_proxy_request(client=client, rp_request=rp_request)
    return rp_response


def extract_ip_from_url(url: httpx.URL) -> str | None:
    """
    Extract an IP address from a URL.

    Args:
        url (httpx.URL): URL to extract IP from.

    Returns:
        str | None: Extracted IP address or None if not found.
    """
    pattern = re.compile(r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})")
    ip_from_url = None
    try:
        ip_from_url = pattern.findall(str(url))[0]
    except (TypeError, IndexError):
        pass
    return ip_from_url
