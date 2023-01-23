from unittest.mock import patch

from typer.testing import CliRunner

from tubecast import settings
from tubecast.core.cli import typer_app


def test_cli_version() -> None:
    """
    Test the CLI version command.
    """
    runner = CliRunner()
    result = runner.invoke(typer_app, ["--version"])
    assert result.exit_code == 0
    assert f"{settings.PACKAGE_NAME} version:" in result.output


def test_cli_main() -> None:
    """
    Test the CLI main command.
    """
    with patch("tubecast.core.cli.start_server") as mock_start_server:
        runner = CliRunner()
        result = runner.invoke(typer_app)
        assert result.exit_code == 0
        mock_start_server.assert_called_once()
