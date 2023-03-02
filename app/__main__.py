from app import logger
from app.core.cli import typer_app


def main():
    logger.info("\n")
    logger.info("--- Start ---")
    logger.info(f"Starting Typer App: '{typer_app.info.name}'...")
    typer_app()


if __name__ == "__main__":
    main()  # pragma: no cover
