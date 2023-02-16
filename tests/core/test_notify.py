from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from telegram.error import BadRequest

from app import settings
from app.core import notify


@patch("app.core.notify.settings.TELEGRAM_API_TOKEN", "valid_token")
@patch("app.core.notify.settings.TELEGRAM_CHAT_ID", 123)
@patch("app.core.notify.settings.NOTIFY_TELEGRAM_ENABLED", True)
async def test_send_telegram_message() -> None:
    """
    Test that the telegram message is sent.
    """
    with patch("telegram.Bot.send_message") as mock_send_message:
        await notify.send_telegram_message("test")
    assert mock_send_message.called


@patch("app.core.notify.settings.NOTIFY_TELEGRAM_ENABLED", True)
@patch("app.core.notify.settings.TELEGRAM_CHAT_ID", 0)
async def test_send_telegram_message_settings_not_set() -> None:
    """
    Test that the logger is called when the settings are not set.
    """
    with patch("app.core.notify.logger") as mock_logger:
        await notify.send_telegram_message("test message")
        mock_logger.warning.assert_called_with(
            "TELEGRAM_API_TOKEN or TELEGRAM_CHAT_ID config variables are not set."
        )


@patch("app.core.notify.settings.TELEGRAM_API_TOKEN", "valid_token")
@patch("app.core.notify.settings.TELEGRAM_CHAT_ID", 123)
async def test_telegram_message_bad_request() -> None:
    """
    Test that the telegram message raises a ValueError when a BadRequest is raised.
    """
    with patch("telegram.Bot.send_message") as mock_send_message:
        mock_send_message.side_effect = BadRequest("test")
        with pytest.raises(ValueError):
            await notify.send_telegram_message("test message")


@patch("app.core.notify.settings.EMAILS_ENABLED", True)
@patch("app.core.notify.settings.NOTIFY_EMAIL_ENABLED", True)
@patch("app.core.notify.settings.NOTIFY_TELEGRAM_ENABLED", True)
async def test_notify() -> None:
    """
    Test that the notify function calls the telegram and email functions.
    """
    with patch("app.core.notify.send_telegram_message") as mock_telegram:
        with patch("app.core.notify.send_email") as mock_email:
            await notify.notify("test message", email=True, telegram=True)

    assert mock_telegram.called
    assert mock_email.called


@patch("app.core.notify.settings.NOTIFY_EMAIL_ENABLED", True)
@patch("app.core.notify.settings.TELEGRAM_CHAT_ID", 123)
async def test_notify_telegram_false() -> None:
    """
    Test that the notify function does not call the telegram function when telegram=False.
    """
    with patch("app.core.notify.send_telegram_message") as mock_telegram:
        with patch("app.core.notify.send_email") as mock_email:
            await notify.notify("test message", telegram=False, email=True)

    assert not mock_telegram.called
    assert mock_email.called


@patch("app.core.notify.settings.NOTIFY_TELEGRAM_ENABLED", True)
@patch("app.core.notify.settings.NOTIFY_EMAIL_ENABLED", True)
async def test_notify_email_false() -> None:
    """
    Test that the notify function does not call the email function when email=False.
    """
    with patch("app.core.notify.send_telegram_message") as mock_telegram:
        with patch("app.core.notify.send_email") as mock_email:
            await notify.notify("test message", email=False)

    assert mock_telegram.called
    assert not mock_email.called


@patch("app.core.notify.settings.TELEGRAM_API_TOKEN", "valid_token")
@patch("app.core.notify.settings.TELEGRAM_CHAT_ID", 123)
@patch("app.core.notify.settings.EMAILS_ENABLED", True)
@patch("app.core.notify.settings.SMTP_USER", "user")
@patch("app.core.notify.settings.SMTP_PASSWORD", "password")
async def test_send_email() -> None:
    """
    Test that the send_email function calls the emails package.
    """
    with patch("emails.message.Message.send") as mock_message:
        notify.send_email(
            email_to="test",
            subject_template="test",
            html_template="test",
        )

    assert mock_message.called
    assert mock_message.call_count == 1


@patch("app.core.notify.settings.EMAILS_ENABLED", False)
async def test_send_email_not_enabled() -> None:
    """
    Test that the send_email function does not call the emails package when emails are not enabled.
    """
    with patch("emails.message.Message.send") as mock_message:
        with pytest.raises(ValueError) as e:
            notify.send_email(
                email_to="test",
                subject_template="test",
                html_template="test",
            )

    assert e.value.args[0] == "Emails are not enabled or email_to is None"
    assert not mock_message.called


@patch("app.core.notify.get_html_template", "")
async def test_send_test_email() -> None:
    """
    Test that the send_test_email function calls the send_email function.
    """
    with patch("app.core.notify.get_html_template") as mock_get_html_template:
        mock_get_html_template.return_value = ""
        with patch("app.core.notify.send_email") as mock_send_email:
            notify.send_test_email(email_to="test@example.com")

    assert mock_send_email.called
    assert mock_send_email.call_count == 1


async def test_send_reset_password_email() -> None:
    """
    Test that the send_reset_password_email function calls the send_email function.
    """
    with patch("app.core.notify.get_html_template") as mock_get_html_template:
        mock_get_html_template.return_value = ""
        with patch("app.core.notify.send_email") as mock_send_email:
            notify.send_reset_password_email(
                email_to="test@example.com", username="test", token="test"
            )

    assert mock_send_email.called
    assert mock_send_email.call_count == 1


async def test_send_new_account_email() -> None:
    """
    Test that the send_new_account_email function calls the send_email function.
    """
    with patch("app.core.notify.get_html_template") as mock_get_html_template:
        mock_get_html_template.return_value = ""
        with patch("app.core.notify.send_email") as mock_send_email:
            notify.send_new_account_email(
                email_to="test@example.com", username="test", password="test"
            )

    assert mock_send_email.called
    assert mock_send_email.call_count == 1


@patch("app.core.notify.settings.NOTIFY_ON_START", True)
async def test_notify_on_start(client: TestClient) -> None:
    """
    Test that the notify_on_start function calls the notify function.
    """
    with patch("app.core.notify.get_html_template") as mock_get_html_template:
        mock_get_html_template.return_value = ""
        with patch("app.core.notify.notify") as mock_notify:
            with client as c:
                c.get("/'")
    assert mock_notify.called
    assert mock_notify.call_count == 1
    assert mock_notify.call_args[1] == {
        "text": f"{settings.PROJECT_NAME}('{settings.ENV_NAME}') started."
    }
