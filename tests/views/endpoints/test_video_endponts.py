from unittest.mock import patch

from fastapi import Request
from sqlmodel import Session

from tubecast.views.endpoints.sources import html_view_sources


async def test_html_view_sources(db_with_sources: Session, test_request: Request) -> None:
    """
    Test that the html_view_sources function returns a response with the correct status code.
    """
    with patch(
        "tubecast.views.endpoints.sources.templates.TemplateResponse"
    ) as mock_template_response:
        await html_view_sources(
            request=test_request,
            db=db_with_sources,
        )

        assert mock_template_response.called

        # Test that the correct arguments are passed to the TemplateResponse
        assert mock_template_response.call_args[0][0] == "view_sources.html"

        response_context = mock_template_response.call_args[0][1]
        assert response_context["request"] == test_request
        assert len(response_context["sources"]) == 3
