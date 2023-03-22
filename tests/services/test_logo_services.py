from pathlib import Path

import pytest

from app.services.logo import create_logo_from_text


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_create_logo_from_text(tmp_path: Path) -> None:
    text = "test\nmultiline\ncase"
    file_path = tmp_path / "logo.png"

    create_logo_from_text(text=text, file_path=file_path)

    # Check that image file exists
    assert file_path.exists()


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_create_logo_from_text2(tmp_path: Path) -> None:
    text = "test test \nmultiline  nmultiline \ncase ncase"
    file_path = tmp_path / "logo.png"

    create_logo_from_text(text=text, file_path=file_path)

    # Check that image file exists
    assert file_path.exists()


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_create_logo_from_text3(tmp_path: Path) -> None:
    text = (
        "test test test test\nmultiline nmultiline nmultiline nmultiline \ncase ncase ncase ncase"
    )
    file_path = tmp_path / "logo.png"

    create_logo_from_text(text=text, file_path=file_path)

    # Check that image file exists
    assert file_path.exists()
