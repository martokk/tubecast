import pytest

from app import paths, settings
from app.views import get_templates


def test_templates_obj_env_globals() -> None:
    templates = get_templates()
    assert templates.env.globals["ENV_NAME"] == settings.ENV_NAME
    assert templates.env.globals["PROJECT_NAME"] == settings.PROJECT_NAME
    assert templates.env.globals["PACKAGE_NAME"] == settings.PACKAGE_NAME
    assert templates.env.globals["PROJECT_DESCRIPTION"] == settings.PROJECT_DESCRIPTION
    assert templates.env.globals["BASE_DOMAIN"] == settings.BASE_DOMAIN
    assert templates.env.globals["BASE_URL"] == settings.BASE_URL
    assert templates.env.globals["VERSION"] == settings.VERSION
