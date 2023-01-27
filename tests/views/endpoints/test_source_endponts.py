from unittest.mock import patch

from fastapi import Request
from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.mock_objects import MOCKED_RUMBLE_SOURCE_1, MOCKED_YOUTUBE_SOURCE_1
from tubecast import settings
from tubecast.views.endpoints.sources import html_view_users_sources


async def test_html_view_users_sources(
    db_with_user: Session,
    client: TestClient,
    test_request: Request,
    normal_user_token_headers: dict[str, str],
) -> None:
    """
    Test that the html_view_users_sources function returns a response with the correct status code.
    """
    # Create 2 new sources for normal test user
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
        json={"url": MOCKED_YOUTUBE_SOURCE_1["url"]},
    )
    assert response.status_code == 201
    response = client.post(
        f"{settings.API_V1_PREFIX}/source/",
        headers=normal_user_token_headers,
        json={"url": MOCKED_RUMBLE_SOURCE_1["url"]},
    )
    assert response.status_code == 201

    # Assert that the response is correct
    with patch(
        "tubecast.views.endpoints.sources.templates.TemplateResponse"
    ) as mock_template_response:
        await html_view_users_sources(request=test_request, db=db_with_user, username="test_user")

        assert mock_template_response.called

        # Test that the correct arguments are passed to the TemplateResponse
        assert mock_template_response.call_args[0][0] == "view_users_sources.html"

        response_context = mock_template_response.call_args[0][1]
        assert response_context["request"] == test_request
        assert len(response_context["sources"]) == 2
