from typing import Any

from unittest.mock import MagicMock, patch

import uvicorn
from fastapi.testclient import TestClient
from typer import Exit

from tubecast import get_version, settings
from tubecast.core.cli import version_callback
from tubecast.core.server import start_server


def test_version_callback(mocker: MagicMock) -> None:
    mock_console = mocker.patch("tubecast.core.cli.console")

    try:
        version_callback(print_version=True)
    except Exit:
        pass
    version = get_version()
    mock_console.print.assert_called_with(
        f"[yellow]{settings.PACKAGE_NAME}[/] version: [bold blue]{version}[/]"
    )


def test_start_server_host_port(monkeypatch: MagicMock) -> None:
    def mock_run(*args: Any, **kwargs: Any) -> None:
        assert kwargs["host"] == settings.SERVER_HOST
        assert kwargs["port"] == settings.SERVER_PORT

    monkeypatch.setattr(uvicorn, "run", mock_run)
    start_server()


def test_start_server_log_level(monkeypatch: MagicMock) -> None:
    def mock_run(*args: Any, **kwargs: Any) -> None:
        assert kwargs["log_level"] == settings.LOG_LEVEL.lower()

    monkeypatch.setattr(uvicorn, "run", mock_run)
    start_server()


def test_start_server() -> None:
    """Tests that the start_server function calls uvicorn.run with the correct arguments."""
    with patch("uvicorn.run") as mock_run:
        start_server()
        mock_run.assert_called_once()
        assert mock_run.call_args[1]["host"] == settings.SERVER_HOST
        assert mock_run.call_args[1]["port"] == settings.SERVER_PORT
        assert mock_run.call_args[1]["log_level"] == settings.LOG_LEVEL.lower()
        assert mock_run.call_args[1]["reload"] == settings.UVICORN_RELOAD
        assert mock_run.call_args[1]["app_dir"] == ""


def test_health_check(client: TestClient) -> None:
    """Test that the health check endpoint returns a 200 status code."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "name": settings.PROJECT_NAME,
        "version": get_version(),
        "description": settings.PROJECT_DESCRIPTION,
    }
