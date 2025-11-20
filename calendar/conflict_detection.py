"""
Calendar conflict detection and resolution.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from calendar.client import list_events

logger = logging.getLogger(__name__)


async def detect_conflicts(
    session,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_event_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Detect conflicts with existing calendar events.
    
    Args:
        session: Database session
        user_id: User ID
        start_time: Proposed start time
        end_time: Proposed end time
        exclude_event_id: Event ID to exclude from conflict check
    
    Returns:
        List of conflicting events
    """
    try:
        events = await list_events(
            session,
            user_id,
            time_min=start_time - timedelta(hours=1),
            time_max=end_time + timedelta(hours=1)
        )
        
        conflicts = []
        for event in events:
            if exclude_event_id and event.get('id') == exclude_event_id:
                continue
            
            event_start = parse_event_time(event.get('start'))
            event_end = parse_event_time(event.get('end'))
            
            if event_start and event_end:
                # Check for overlap
                if (start_time < event_end and end_time > event_start):
                    conflicts.append({
                        'id': event.get('id'),
                        'title': event.get('summary'),
                        'start': event_start,
                        'end': event_end,
                        'overlap_start': max(start_time, event_start),
                        'overlap_end': min(end_time, event_end)
                    })
        
        return conflicts
    except Exception as e:
        logger.error(f"Error detecting conflicts: {e}")
        return []


def parse_event_time(time_str: Optional[str]) -> Optional[datetime]:
    """
    Parse event time string to datetime.
    
    Args:
        time_str: Time string (ISO format or date)
    
    Returns:
        Datetime object or None
    """
    if not time_str:
        return None
    
    try:
        # Try ISO format with time
        if 'T' in time_str:
            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        # Try date only
        else:
            return datetime.fromisoformat(time_str)
    except Exception:
        return None


async def find_available_slots(
    session,
    user_id: int,
    duration_minutes: int,
    start_date: datetime,
    end_date: datetime,
    work_start_hour: int = 8,
    work_end_hour: int = 20
) -> List[Tuple[datetime, datetime]]:
    """
    Find available time slots.
    
    Args:
        session: Database session
        user_id: User ID
        duration_minutes: Required duration in minutes
        start_date: Start of search window
        end_date: End of search window
        work_start_hour: Work day start hour
        work_end_hour: Work day end hour
    
    Returns:
        List of (start, end) datetime tuples
    """
    try:
        events = await list_events(
            session,
            user_id,
            time_min=start_date,
            time_max=end_date
        )
        
        # Sort events by start time
        events.sort(key=lambda e: parse_event_time(e.get('start')) or datetime.min)
        
        available_slots = []
        current = start_date
        
        for event in events:
            event_start = parse_event_time(event.get('start'))
            event_end = parse_event_time(event.get('end'))
            
            if not event_start or not event_end:
                continue
            
            # Check if there's a gap before this event
            if current < event_start:
                gap_minutes = (event_start - current).total_seconds() / 60
                if gap_minutes >= duration_minutes:
                    # Check if within work hours
                    if is_within_work_hours(current, work_start_hour, work_end_hour):
                        slot_end = current + timedelta(minutes=duration_minutes)
                        if slot_end <= event_start:
                            available_slots.append((current, slot_end))
            
            current = max(current, event_end)
        
        # Check if there's time after last event
        if current < end_date:
            gap_minutes = (end_date - current).total_seconds() / 60
            if gap_minutes >= duration_minutes:
                if is_within_work_hours(current, work_start_hour, work_end_hour):
                    slot_end = current + timedelta(minutes=duration_minutes)
                    if slot_end <= end_date:
                        available_slots.append((current, slot_end))
        
        return available_slots[:5]  # Return top 5 slots
    except Exception as e:
        logger.error(f"Error finding available slots: {e}")
        return []


def is_within_work_hours(dt: datetime, start_hour: int, end_hour: int) -> bool:
    """
    Check if datetime is within work hours.
    
    Args:
        dt: Datetime to check
        start_hour: Work start hour
        end_hour: Work end hour
    
    Returns:
        True if within work hours
    """
    hour = dt.hour
    return start_hour <= hour < end_hour

