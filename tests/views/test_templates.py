import pytest

from app import settings
from app.views.templates import get_templates
from app.views.templates.filters import (
    filter_humanize,
    filter_humanize_color_class_rumble,
    filter_humanize_color_class_youtube,
    filter_service_badge_color,
)


def test_templates_obj_env_globals() -> None:
    templates = get_templates()
    assert templates.env.globals["ENV_NAME"] == settings.ENV_NAME
    assert templates.env.globals["PROJECT_NAME"] == settings.PROJECT_NAME
    assert templates.env.globals["PACKAGE_NAME"] == settings.PACKAGE_NAME
    assert templates.env.globals["PROJECT_DESCRIPTION"] == settings.PROJECT_DESCRIPTION
    assert templates.env.globals["BASE_DOMAIN"] == settings.BASE_DOMAIN
    assert templates.env.globals["BASE_URL"] == settings.BASE_URL
    assert templates.env.globals["VERSION"] == ""

    assert templates.env.filters["humanize"] == filter_humanize
    assert (
        templates.env.filters["humanize_color_class_youtube"] == filter_humanize_color_class_youtube
    )
    assert (
        templates.env.filters["humanize_color_class_rumble"] == filter_humanize_color_class_rumble
    )
    assert templates.env.filters["service_badge_color"] == filter_service_badge_color
