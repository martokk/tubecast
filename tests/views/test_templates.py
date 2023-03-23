from datetime import datetime, timedelta

import pytest

from app import handlers, settings
from app.views.templates import get_templates
from app.views.templates.filters import (
    filter_humanize,
    filter_humanize_color_class,
    filter_humanize_color_class_rumble,
    filter_humanize_color_class_youtube,
    filter_service_badge_color,
)


def test_templates_obj_env_globals() -> None:
    templates = get_templates()
    assert templates.env.globals["ENV_NAME"] == settings.ENV_NAME
    assert templates.env.globals["PROJECT_NAME"] == settings.PROJECT_NAME
    assert templates.env.globals["PACKAGE_NAME"] == settings.PACKAGE_NAME
    assert templates.env.globals["PROJECT_DESCRIPTION"] == settings.PROJECT_DESCRIPTION
    assert templates.env.globals["BASE_DOMAIN"] == settings.BASE_DOMAIN
    assert templates.env.globals["BASE_URL"] == settings.BASE_URL
    assert templates.env.globals["VERSION"] == ""

    assert templates.env.filters["humanize"] == filter_humanize
    assert (
        templates.env.filters["humanize_color_class_youtube"] == filter_humanize_color_class_youtube
    )
    assert (
        templates.env.filters["humanize_color_class_rumble"] == filter_humanize_color_class_rumble
    )
    assert templates.env.filters["service_badge_color"] == filter_service_badge_color


def test_filter_humanize():
    now = datetime.utcnow()

    # Testing 'just now'
    assert filter_humanize(now - timedelta(seconds=1)) == "just now"
    assert filter_humanize(now - timedelta(seconds=9)) == "just now"

    # Testing seconds ago
    assert filter_humanize(now - timedelta(seconds=45)) == "45 sec ago"
    assert filter_humanize(now - timedelta(minutes=1, seconds=45)) == "a minute ago"
    assert filter_humanize(now - timedelta(minutes=10, seconds=45)) == "10 min ago"

    # Testing minutes and hours ago
    assert filter_humanize(now - timedelta(hours=1)) == "an hour ago"
    assert filter_humanize(now - timedelta(hours=4, minutes=30)) == "4 hours ago"
    assert filter_humanize(now - timedelta(days=1)) == "Yesterday"

    # Testing last week
    assert filter_humanize(now - timedelta(days=6)) == "6 days ago"
    assert filter_humanize(now - timedelta(days=7)) == "1 week ago"

    # Testing last month
    assert filter_humanize(now - timedelta(days=25)) == "3 weeks ago"
    assert filter_humanize(now - timedelta(days=31)) == "1 months ago"

    # Testing last year
    assert filter_humanize(now - timedelta(days=365)) == "1 years ago"


def test_filter_humanize_color_class():
    now = datetime.utcnow()
    warning_seconds = 60 * 60  # 1 hour
    danger_seconds = 2 * 60 * 60  # 2 hours
    success_seconds = 60  # 60 seconds

    assert (
        filter_humanize_color_class(
            dt=now - timedelta(seconds=danger_seconds),
            warning_seconds=warning_seconds,
            danger_seconds=danger_seconds,
            success_seconds=success_seconds,
        )
        == "text-danger"
    )
    assert (
        filter_humanize_color_class(
            dt=now - timedelta(seconds=warning_seconds + 1),
            warning_seconds=warning_seconds,
            danger_seconds=danger_seconds,
            success_seconds=success_seconds,
        )
        == "text-warning"
    )
    assert (
        filter_humanize_color_class(
            dt=now - timedelta(seconds=success_seconds + 1),
            warning_seconds=warning_seconds,
            danger_seconds=danger_seconds,
            success_seconds=success_seconds,
        )
        == "text-body-tertiary"
    )
    assert (
        filter_humanize_color_class(
            dt=now - timedelta(seconds=1),
            warning_seconds=warning_seconds,
            danger_seconds=danger_seconds,
            success_seconds=success_seconds,
        )
        == "text-success"
    )


async def test_filter_humanize_color_class_rumble() -> None:
    now = datetime.utcnow()
    handler = handlers.rumble.RumbleHandler()
    warning_hours = int(handler.REFRESH_UPDATE_INTERVAL_HOURS - 12)
    danger_hours = int(handler.REFRESH_UPDATE_INTERVAL_HOURS)

    assert (
        filter_humanize_color_class_rumble(dt=now - timedelta(hours=danger_hours)) == "text-danger"
    )
    assert (
        filter_humanize_color_class_rumble(dt=now - timedelta(hours=warning_hours + 1))
        == "text-warning"
    )
    assert (
        filter_humanize_color_class_rumble(dt=now - timedelta(hours=warning_hours - 1))
        == "text-body-tertiary"
    )
    assert filter_humanize_color_class_rumble(dt=now - timedelta(seconds=1)) == "text-success"


def test_filter_service_badge_color():
    # Test service name = "Rumble"
    assert filter_service_badge_color("Rumble") == "bg-rumble"

    # Test service name = "Youtube"
    assert filter_service_badge_color("Youtube") == "bg-youtube"

    # Test service name not equal to "Rumble" or "Youtube"
    assert filter_service_badge_color("Some Other Service") == "bg-light"
