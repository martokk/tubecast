from fastapi.templating import Jinja2Templates

from tubecast import paths, settings


def get_templates() -> Jinja2Templates:
    """
    Create Jinja2Templates object and add global variables to templates.

    Returns:
        Jinja2Templates: Jinja2Templates object.
    """
    # Create Jinja2Templates object
    templates = Jinja2Templates(directory=paths.TEMPLATES_PATH)

    # Add global variables to templates
    if settings.ENV_NAME == "production":
        templates.env.globals["PROJECT_NAME"] = settings.PROJECT_NAME
    else:
        templates.env.globals["PROJECT_NAME"] = f"{settings.PROJECT_NAME} ({settings.ENV_NAME})"
    templates.env.globals["PROJECT_DESCRIPTION"] = settings.PROJECT_DESCRIPTION
    return templates


templates = get_templates()
