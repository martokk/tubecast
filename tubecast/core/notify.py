from typing import Any

from pathlib import Path

import emails
from emails.template import JinjaTemplate  # type: ignore
from telegram import Bot
from telegram.error import BadRequest

from python_fastapi_stack import logger, paths, settings


async def notify(
    text: str, telegram: bool = True, email: bool = settings.EMAILS_ENABLED
) -> dict[str, Any]:
    """
    Sends a notification via Telegram and email.

    Args:
        text (str): The notification text to send.
        telegram (bool): Whether to send the notification via Telegram. Defaults to True.
        email (bool): Whether to send the notification via email. Defaults to True.

    Returns:
        dict[str, Any]: The response from the notification types APIs.

    """
    response = {}
    if telegram:
        response["telegram"] = await send_telegram_message(text=text)
    if email:
        response["email"] = send_email(
            email_to=settings.NOTIFY_EMAIL_TO,
            subject_template="Server Notification",
            html_template=text,
            environment={"name": f"{settings.PROJECT_NAME}"},
        )
    return response


async def send_telegram_message(text: str) -> Any:
    """Sends a message via Telegram using the given text as the message's content.
    Telegram API token and chat ID must be set before calling this function.

    Args:
        text (str): The message text to send.

    Returns:
        Any : the message object

    Raises:
        ValueError: If the chat with the Telegram bot has not been initialized by the user
    """
    if not settings.TELEGRAM_API_TOKEN or settings.TELEGRAM_CHAT_ID == 0:
        logger.warning("TELEGRAM_API_TOKEN or TELEGRAM_CHAT_ID config variables are not set.")
        return None

    bot = Bot(token=settings.TELEGRAM_API_TOKEN)

    try:
        return await bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=text)
    except BadRequest as e:
        raise ValueError(
            "The chat with the Telegram bot has not been first initialized by the user. "
            "Please start a conversation with the bot before trying to send a message"
        ) from e


def send_email(
    email_to: str | None,
    subject_template: str = "",
    html_template: str = "",
    environment: dict[str, Any] | None = None,
) -> Any:
    """
    Sends an email using the provided templates and environment variables.

    Args:
        email_to (str): The email address to send the email to.
        subject_template (str): The subject template. Defaults to "".
        html_template (str): The HTML template. Defaults to "".
        environment (dict[str, Any] | None): The environment variables to use when
            rendering the templates. Defaults to None.

    Returns:
        Any: The email response.

    Raises:
        ValueError: If the email variables are not set.
    """

    if not settings.EMAILS_ENABLED or email_to is None:
        raise ValueError("Emails are not enabled or email_to is None")

    # Build the email
    message = emails.Message(  # type: ignore
        subject=JinjaTemplate(subject_template),
        html=JinjaTemplate(html_template),
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )

    # Build the SMTP options
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD

    if not environment:
        environment = {}

    # Send the email
    response = message.send(to=email_to, render=environment, smtp=smtp_options)
    logger.info(f"send email result: {response}")
    return response


def get_html_template(template: Path) -> str:
    return template.read_text(encoding="utf8")  # pragma: no cover


def send_test_email(email_to: str) -> None:
    send_email(
        email_to=email_to,
        subject_template=f"{settings.PROJECT_NAME} - Test email",
        html_template=get_html_template(template=paths.EMAIL_TEMPLATES_PATH / "test_email.mjml"),
        environment={"project_name": settings.PROJECT_NAME, "email": email_to},
    )


def send_reset_password_email(email_to: str, username: str, token: str) -> None:
    send_email(
        email_to=email_to,
        subject_template=f"{settings.PROJECT_NAME} - Password recovery for user {username}",
        html_template=get_html_template(
            template=paths.EMAIL_TEMPLATES_PATH / "reset_password.mjml"
        ),
        environment={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": f"{settings.BASE_URL}/reset-password?token={token}",
        },
    )


def send_new_account_email(email_to: str, username: str, password: str) -> None:
    send_email(
        email_to=email_to,
        subject_template=f"{settings.PROJECT_NAME} - New account for user {username}",
        html_template=get_html_template(template=paths.EMAIL_TEMPLATES_PATH / "new_account.mjml"),
        environment={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": settings.SERVER_HOST,
        },
    )
