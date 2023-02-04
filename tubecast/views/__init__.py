from fastapi.templating import Jinja2Templates

from tubecast import paths, settings

# Create Jinja2Templates object
templates = Jinja2Templates(directory=paths.TEMPLATES_PATH)

# Add global variables to templates
if settings.ENV_NAME == "production":
    templates.env.globals["PROJECT_NAME"] = settings.PROJECT_NAME
else:
    templates.env.globals["PROJECT_NAME"] = f"{settings.PROJECT_NAME} ({settings.ENV_NAME})"
templates.env.globals["PROJECT_DESCRIPTION"] = settings.PROJECT_DESCRIPTION
