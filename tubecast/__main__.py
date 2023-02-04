from python_fastapi_stack import logger
from python_fastapi_stack.core.cli import typer_app


def main():
    logger.info("--- Start ---")
    logger.info(f"Starting Typer App: '{typer_app.info.name}'...")
    typer_app()


if __name__ == "__main__":
    main()  # pragma: no cover
