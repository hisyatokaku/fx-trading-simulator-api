"""Date and time utility functions."""

from datetime import datetime, timedelta
from typing import Optional

from dateutil import parser as date_parser


def parse_datetime(dt_string: str) -> datetime:
    """Parse a datetime string into a datetime object.

    Supports various formats including ISO 8601.
    """
    return date_parser.parse(dt_string)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%dT%H:%M:%S") -> str:
    """Format a datetime object to string."""
    return dt.strftime(fmt)


def add_interval(dt: datetime, seconds: int) -> datetime:
    """Add time interval to datetime, skipping weekends for day-sized intervals."""
    result = dt + timedelta(seconds=seconds)
    if seconds >= 86400:
        while result.weekday() >= 5:  # 5=Saturday, 6=Sunday
            result += timedelta(days=1)
    return result


def get_nearest_timestamp(target: datetime, available: list[datetime]) -> Optional[datetime]:
    """Find the nearest timestamp from available timestamps.

    Returns the closest timestamp that is less than or equal to target.
    If no such timestamp exists, returns None.
    """
    if not available:
        return None

    # Filter timestamps <= target
    valid = [ts for ts in available if ts <= target]
    if not valid:
        return None

    # Return the most recent one
    return max(valid)
