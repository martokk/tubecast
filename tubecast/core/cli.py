import typer
from rich.console import Console

from python_fastapi_stack import logger, settings, version
from python_fastapi_stack.core.server import start_server

# from python_fastapi_stack.core.app import app

# Configure Rich Console
console = Console()

# Configure Typer
typer_app = typer.Typer(
    name=settings.PACKAGE_NAME,
    help=settings.PROJECT_DESCRIPTION,
    add_completion=False,
)


# Typer Command Callbacks
def version_callback(print_version: bool) -> None:
    """
    Print the version of the package.

    Args:
        print_version: bool : If true, print version of the package and exit.

    Raises:
        Exit: Exit the application.
    """
    if print_version:
        console.print(f"[yellow]{settings.PACKAGE_NAME}[/] version: [bold blue]{version}[/]")
        raise typer.Exit()


# Typer Commands
@typer_app.command()
def main(
    print_version: bool = typer.Option(  # pylint: disable=unused-argument
        None,
        "-v",
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Prints the version of the '{APP_NAME}' package.",
    ),
) -> None:
    """
    Main entrypoint into application
    This function starts the server and raises an error if not implemented.

    Args:
        print_version: bool : If true, print version of the package and exit.
    """

    # Start Uvicorn
    logger.info("Starting Server...")
    start_server()
