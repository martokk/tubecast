import httpx
from fastapi import status, HTTPException
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from tubecast import logger

client = httpx.AsyncClient()


async def reverse_proxy(url: str, request: Request) -> StreamingResponse:
    """
    Reverse proxy a request to a given URL.

    Args:
        url: URL to reverse proxy to.
        request: Request to reverse proxy.

    Returns:
        StreamingResponse: Response from reverse proxy.

    Raises:
        ValueError: If URL is invalid.
    """
    url = httpx.URL(url=url)  # type: ignore

    rp_request = client.build_request(method=request.method, url=url)

    # Copy headers from original request to reverse proxy request
    try:
        rp_response = await client.send(rp_request, stream=True)
    except httpx.ConnectError as e:
        raise ValueError("Invalid URL") from e

    if rp_response.status_code != status.HTTP_200_OK:
        logger.error(f"Reverse proxy request failed with status code {rp_response.status_code}")
        logger.error(f"{rp_response=}")
        raise HTTPException(status_code=rp_response.status_code)

    return StreamingResponse(
        rp_response.aiter_raw(),
        status_code=rp_response.status_code,
        headers=rp_response.headers,
        background=BackgroundTask(rp_response.aclose),
    )
