"""
Input validation helpers for edge case handling.
According to TESTING_AND_REFINEMENT_PLAN.md
"""
import logging
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


def validate_task_title(title: str) -> Tuple[bool, Optional[str]]:
    """
    Validate task title.
    
    Args:
        title: Task title to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not title:
        return False, "Task title cannot be empty. Please provide a title."
    
    title = title.strip()
    
    if not title:
        return False, "Task title cannot be empty. Please provide a title."
    
    if len(title) > 500:
        return False, f"Task title is too long (max 500 characters). Your title has {len(title)} characters."
    
    # Check for only whitespace or special characters
    if not any(c.isalnum() for c in title):
        return False, "Task title must contain at least one letter or number."
    
    return True, None


def validate_pillar_name(pillar: str, available_pillars: list = None) -> Tuple[bool, Optional[str]]:
    """
    Validate pillar/category name.
    
    Args:
        pillar: Pillar name to validate
        available_pillars: List of available pillars (optional)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not pillar:
        return False, "Pillar name cannot be empty."
    
    pillar = pillar.strip().lower()
    
    if len(pillar) > 50:
        return False, f"Pillar name is too long (max 50 characters)."
    
    # Check for only whitespace or special characters
    if not any(c.isalnum() for c in pillar):
        return False, "Pillar name must contain at least one letter or number."
    
    # Check if in available pillars (if provided)
    if available_pillars:
        available_lower = [p.lower() for p in available_pillars]
        if pillar not in available_lower:
            return False, f"Invalid pillar '{pillar}'. Available pillars: {', '.join(available_pillars)}"
    
    return True, None


def validate_priority(priority: str) -> Tuple[bool, Optional[str]]:
    """
    Validate priority value.
    
    Args:
        priority: Priority value to validate
    
    Returns:
        Tuple of (is_valid, error_message, normalized_priority)
    """
    if not priority:
        return False, "Priority cannot be empty.", None
    
    priority = priority.strip().lower()
    
    valid_priorities = ["low", "medium", "high", "urgent"]
    
    if priority not in valid_priorities:
        # Try to match partial or similar
        if "urgent" in priority or "critical" in priority:
            return True, None, "urgent"
        elif "high" in priority:
            return True, None, "high"
        elif "medium" in priority or "normal" in priority:
            return True, None, "medium"
        elif "low" in priority:
            return True, None, "low"
        else:
            return False, f"Invalid priority '{priority}'. Valid options: {', '.join(valid_priorities)}", None
    
    return True, None, priority


def validate_due_date(date_str: str, allow_past: bool = False) -> Tuple[bool, Optional[str], Optional[datetime]]:
    """
    Validate due date string.
    
    Args:
        date_str: Date string to validate
        allow_past: Whether to allow past dates
    
    Returns:
        Tuple of (is_valid, error_message, parsed_date)
    """
    if not date_str:
        return True, None, None  # Optional field
    
    date_str = date_str.strip()
    
    if not date_str or date_str.lower() in ["none", "no", "n/a"]:
        return True, None, None
    
    try:
        parsed_date = date_parser.parse(date_str)
        
        # Check if past date (unless allowed)
        if not allow_past and parsed_date < datetime.utcnow():
            return False, f"The due date '{date_str}' is in the past. Please provide a future date.", None
        
        return True, None, parsed_date
        
    except Exception as e:
        return False, f"Could not parse date '{date_str}'. Please use formats like 'tomorrow', 'Dec 25', 'next week', etc.", None


def validate_duration(duration_str: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Validate duration string and convert to minutes.
    
    Args:
        duration_str: Duration string to validate (e.g., "2 hours", "30 minutes")
    
    Returns:
        Tuple of (is_valid, error_message, duration_minutes)
    """
    if not duration_str:
        return True, None, None  # Optional field
    
    duration_str = duration_str.strip()
    
    if not duration_str or duration_str.lower() in ["none", "no", "n/a"]:
        return True, None, None
    
    try:
        import re
        
        duration_str_lower = duration_str.lower()
        
        # Pattern: "2 hours" or "2h"
        hour_pattern = r'(\d+(?:\.\d+)?)\s*(?:hours?|h)'
        hour_match = re.search(hour_pattern, duration_str_lower)
        hours = float(hour_match.group(1)) if hour_match else 0
        
        # Pattern: "30 minutes" or "30m"
        min_pattern = r'(\d+)\s*(?:minutes?|mins?|m)'
        min_match = re.search(min_pattern, duration_str_lower)
        minutes = int(min_match.group(1)) if min_match else 0
        
        # If no patterns matched, try to parse as number
        if hours == 0 and minutes == 0:
            try:
                # Try as minutes
                total_minutes = int(duration_str)
                if total_minutes > 0:
                    return True, None, total_minutes
            except ValueError:
                pass
        
        total_minutes = int(hours * 60) + minutes
        
        if total_minutes <= 0:
            return False, f"Duration must be greater than 0. Got: '{duration_str}'", None
        
        # Maximum duration check (e.g., 24 hours = 1440 minutes)
        if total_minutes > 1440:
            return False, f"Duration is too long (max 24 hours / 1440 minutes). Got: {total_minutes} minutes.", None
        
        return True, None, total_minutes
        
    except Exception as e:
        return False, f"Could not parse duration '{duration_str}'. Please use formats like '2 hours', '30 minutes', etc.", None


def validate_message_length(text: str, max_length: int = 4096) -> Tuple[bool, Optional[str]]:
    """
    Validate message length for Telegram (max 4096 chars).
    
    Args:
        text: Text to validate
        max_length: Maximum length allowed
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text:
        return True, None
    
    if len(text) > max_length:
        return False, f"Message is too long (max {max_length} characters). Your message has {len(text)} characters."
    
    return True, None


def validate_work_hours(start_hour: int, end_hour: int) -> Tuple[bool, Optional[str]]:
    """
    Validate work hours.
    
    Args:
        start_hour: Start hour (0-23)
        end_hour: End hour (0-23)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not (0 <= start_hour <= 23):
        return False, f"Start hour must be between 0 and 23. Got: {start_hour}"
    
    if not (0 <= end_hour <= 23):
        return False, f"End hour must be between 0 and 23. Got: {end_hour}"
    
    if start_hour >= end_hour:
        return False, f"Start hour ({start_hour}) must be before end hour ({end_hour})."
    
    return True, None


def validate_timezone(timezone_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validate timezone string.
    
    Args:
        timezone_str: Timezone string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not timezone_str:
        return False, "Timezone cannot be empty."
    
    timezone_str = timezone_str.strip()
    
    try:
        import pytz
        pytz.timezone(timezone_str)
        return True, None
    except pytz.exceptions.UnknownTimeZoneError:
        # Try common aliases
        timezone_aliases = {
            "pst": "America/Los_Angeles",
            "pdt": "America/Los_Angeles",
            "est": "America/New_York",
            "edt": "America/New_York",
            "gmt": "UTC",
            "utc": "UTC",
        }
        
        alias = timezone_str.lower()
        if alias in timezone_aliases:
            return True, None
        
        return False, f"Unknown timezone '{timezone_str}'. Please use a valid timezone like 'America/New_York', 'Europe/London', 'UTC', etc."


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input by trimming whitespace and optionally truncating.
    
    Args:
        text: Text to sanitize
        max_length: Maximum length (optional)
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    text = text.strip()
    
    if max_length and len(text) > max_length:
        text = text[:max_length].strip()
    
    return text


def validate_empty_or_whitespace(text: str) -> bool:
    """
    Check if text is empty or only whitespace.
    
    Args:
        text: Text to check
    
    Returns:
        True if empty/whitespace, False otherwise
    """
    return not text or not text.strip()

