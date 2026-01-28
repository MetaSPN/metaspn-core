"""Date utilities for MetaSPN."""

from datetime import datetime, date, timedelta
from typing import Optional, Union


def parse_date(date_str: str) -> datetime:
    """Parse a date string into a datetime object.
    
    Supports multiple formats:
        - ISO 8601: 2024-01-15T10:30:00
        - Date only: 2024-01-15
        - US format: 01/15/2024
        - Compact: 20240115
    
    Args:
        date_str: Date string to parse
    
    Returns:
        Parsed datetime object
    
    Raises:
        ValueError: If format is not recognized
    """
    # Try ISO format first
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y%m%d",
        "%Y-%m-%d %H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try fromisoformat as fallback (handles more ISO variants)
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        pass
    
    raise ValueError(f"Unable to parse date: {date_str}")


def format_date(
    dt: Union[datetime, date],
    format_str: str = "%Y-%m-%d",
) -> str:
    """Format a datetime object as a string.
    
    Args:
        dt: datetime or date object
        format_str: Format string (strftime format)
    
    Returns:
        Formatted date string
    
    Example:
        >>> format_date(datetime.now(), "%Y-%m-%d")
        '2024-01-15'
    """
    return dt.strftime(format_str)


def days_between(
    start: Union[datetime, date],
    end: Union[datetime, date],
) -> int:
    """Calculate days between two dates.
    
    Args:
        start: Start date
        end: End date
    
    Returns:
        Number of days between dates (can be negative)
    """
    if isinstance(start, datetime):
        start = start.date()
    if isinstance(end, datetime):
        end = end.date()
    
    return (end - start).days


def is_within_days(
    dt: Union[datetime, date],
    days: int,
    reference: Optional[Union[datetime, date]] = None,
) -> bool:
    """Check if a date is within N days of a reference date.
    
    Args:
        dt: Date to check
        days: Number of days
        reference: Reference date (defaults to today)
    
    Returns:
        True if dt is within days of reference
    """
    if reference is None:
        reference = datetime.now()
    
    diff = abs(days_between(dt, reference))
    return diff <= days


def get_week_start(
    dt: Optional[Union[datetime, date]] = None,
    week_start_day: int = 0,  # 0 = Monday
) -> date:
    """Get the start of the week for a given date.
    
    Args:
        dt: Date (defaults to today)
        week_start_day: Day week starts (0=Monday, 6=Sunday)
    
    Returns:
        Date of week start
    """
    if dt is None:
        dt = datetime.now()
    if isinstance(dt, datetime):
        dt = dt.date()
    
    days_since_start = (dt.weekday() - week_start_day) % 7
    return dt - timedelta(days=days_since_start)


def get_month_start(dt: Optional[Union[datetime, date]] = None) -> date:
    """Get the first day of the month for a given date.
    
    Args:
        dt: Date (defaults to today)
    
    Returns:
        First day of month
    """
    if dt is None:
        dt = datetime.now()
    if isinstance(dt, datetime):
        dt = dt.date()
    
    return date(dt.year, dt.month, 1)


def date_range(
    start: Union[datetime, date],
    end: Union[datetime, date],
) -> list[date]:
    """Generate a list of dates between start and end (inclusive).
    
    Args:
        start: Start date
        end: End date
    
    Returns:
        List of dates
    """
    if isinstance(start, datetime):
        start = start.date()
    if isinstance(end, datetime):
        end = end.date()
    
    if start > end:
        start, end = end, start
    
    dates = []
    current = start
    while current <= end:
        dates.append(current)
        current += timedelta(days=1)
    
    return dates


def relative_time(dt: datetime) -> str:
    """Get a human-readable relative time string.
    
    Args:
        dt: Datetime to describe
    
    Returns:
        Relative time string like "2 hours ago"
    """
    now = datetime.now()
    diff = now - dt
    
    seconds = int(diff.total_seconds())
    
    if seconds < 0:
        return "in the future"
    elif seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = seconds // 604800
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:
        months = seconds // 2592000
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = seconds // 31536000
        return f"{years} year{'s' if years != 1 else ''} ago"
