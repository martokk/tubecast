import pytest
from tubecast import paths, settings
from tubecast.views import get_templates


def test_templates_obj_env_globals() -> None:
    settings.ENV_NAME = "production"
    templates = get_templates()
    assert templates.env.globals["PROJECT_NAME"] == settings.PROJECT_NAME

    settings.ENV_NAME = "dev"
    templates = get_templates()
    assert templates.env.globals["PROJECT_NAME"] == f"{settings.PROJECT_NAME} ({settings.ENV_NAME})"
