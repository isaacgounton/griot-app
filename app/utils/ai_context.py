"""
AI Context Utilities

Provides common context information for AI prompts, including current date and time.
"""

from datetime import datetime
import pytz


def get_current_context() -> str:
    """
    Get current date and time context for AI prompts.
    
    Returns:
        str: Formatted current date and time string for AI context
    """
    now = datetime.now(pytz.UTC)
    local_date = now.strftime('%A, %B %d, %Y')
    local_time = now.strftime('%H:%M UTC')
    
    return f"Current date and time: {local_date} at {local_time}"


def get_date_context() -> str:
    """
    Get just the current date for AI prompts.
    
    Returns:
        str: Formatted current date string
    """
    now = datetime.now(pytz.UTC)
    return f"Today's date: {now.strftime('%A, %B %d, %Y')}"


def get_time_context() -> str:
    """
    Get just the current time for AI prompts.
    
    Returns:
        str: Formatted current time string
    """
    now = datetime.now(pytz.UTC)
    return f"Current time: {now.strftime('%H:%M UTC')}"


def get_year() -> int:
    """
    Get the current year.
    
    Returns:
        int: Current year
    """
    return datetime.now(pytz.UTC).year