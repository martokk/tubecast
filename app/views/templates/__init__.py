from fastapi.templating import Jinja2Templates

from app import paths
from app.models.settings import Settings as _Settings
from app.views.templates.filters import (
    filter_humanize,
    filter_humanize_color_class_rumble,
    filter_humanize_color_class_youtube,
    filter_service_badge_color,
)

settings = _Settings()  # type: ignore


def get_templates() -> Jinja2Templates:
    """
    Create Jinja2Templates object and add global variables to templates.

    Returns:
        Jinja2Templates: Jinja2Templates object.
    """
    # Create Jinja2Templates object
    templates = Jinja2Templates(directory=paths.TEMPLATES_PATH)

    # Add custom filters to templates
    templates.env.filters["humanize"] = filter_humanize
    templates.env.filters["humanize_color_class_youtube"] = filter_humanize_color_class_youtube
    templates.env.filters["humanize_color_class_rumble"] = filter_humanize_color_class_rumble
    templates.env.filters["service_badge_color"] = filter_service_badge_color

    # Add global variables to templates
    templates.env.globals["PROJECT_NAME"] = settings.PROJECT_NAME
    templates.env.globals["ENV_NAME"] = settings.ENV_NAME
    templates.env.globals["PACKAGE_NAME"] = settings.PACKAGE_NAME
    templates.env.globals["PROJECT_DESCRIPTION"] = settings.PROJECT_DESCRIPTION
    templates.env.globals["BASE_DOMAIN"] = settings.BASE_DOMAIN
    templates.env.globals["BASE_URL"] = settings.BASE_URL
    templates.env.globals["VERSION"] = settings.VERSION

    return templates
