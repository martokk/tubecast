from datetime import datetime

from app.handlers import get_handler_from_string


def filter_humanize(dt: datetime) -> str:
    """
    Jinja Filter to convert datetime to human readable string.

    Args:
        dt (datetime): datetime object.

    Returns:
        str: pretty string like 'an hour ago', 'Yesterday',
            '3 months ago', 'just now', etc
    """
    now = datetime.utcnow()
    diff = now - dt
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ""

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(int(second_diff)) + " sec ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(int(second_diff / 60)) + " min ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(int(second_diff / 3600)) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 14:
        return str(int(day_diff / 7)) + " week ago"
    if day_diff < 31:
        return str(int(day_diff / 7)) + " weeks ago"
    if day_diff < 365:
        return str(int(day_diff / 30)) + " months ago"
    return str(int(day_diff / 365)) + " years ago"


def filter_humanize_color_class(
    dt: datetime, warning_seconds: int, danger_seconds: int, success_seconds: int = 20
) -> str:
    """
    Jinja Filter to convert datetime to color class.
    Used to colorize the "humanize" filter.

    Args:
        dt (datetime): datetime object.
        warning_seconds (int): seconds to colorize as warning
        danger_seconds (int): seconds to colorize as danger
        success_seconds (int): seconds to colorize as success

    Returns:
        str: color class like 'text-danger', 'text-body-tertiary', etc
    """
    delta = datetime.utcnow() - dt
    delta_total_seconds = delta.total_seconds()

    if delta_total_seconds > danger_seconds:
        return "text-danger"
    if delta_total_seconds > warning_seconds:
        return "text-warning"
    if delta_total_seconds > success_seconds:
        return "text-body-tertiary"
    return "text-success"


def filter_humanize_color_class_rumble(dt: datetime) -> str:
    """
    Jinja Filter to convert datetime to color class for YouTube Handler.

    Args:
        dt (datetime): datetime object.

    Returns:
        str: color class like 'text-danger', 'text-body-tertiary', etc
    """
    handler = get_handler_from_string("RumbleHandler")
    warning_hours = int(handler.REFRESH_INTERVAL_HOURS - 12)
    danger_hours = int(handler.REFRESH_INTERVAL_HOURS)

    return filter_humanize_color_class(
        dt=dt,
        warning_seconds=warning_hours * 60 * 60,
        danger_seconds=danger_hours * 60 * 60,
    )


def filter_humanize_color_class_youtube(dt: datetime) -> str:
    """
    Jinja Filter to convert datetime to color class for YouTube Handler.

    Args:
        dt (datetime): datetime object.

    Returns:
        str: color class like 'text-danger', 'text-body-tertiary', etc
    """
    handler = get_handler_from_string("YoutubeHandler")
    warning_hours = int(handler.REFRESH_INTERVAL_HOURS - 1)
    danger_hours = int(handler.REFRESH_INTERVAL_HOURS + 1)

    return filter_humanize_color_class(
        dt=dt,
        warning_seconds=warning_hours * 60 * 60,
        danger_seconds=danger_hours * 60 * 60,
    )


def filter_service_badge_color(service_name: str) -> str:
    """
    Jinja Filter to convert service name to color class.

    Args:
        service_name (str): service name.

    Returns:
        str: color class like 'text-danger', 'text-body-tertiary', etc
    """
    if service_name == "Rumble":
        return "bg-rumble"
    if service_name == "Youtube":
        return "bg-youtube"
    return "bg-light"
