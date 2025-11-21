"""
Calendar synchronization.
"""
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from google_calendar.client import list_events
from google_calendar.auth import get_user_credentials
from database.models import CalendarEvent, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def sync_calendar(
    session: AsyncSession,
    user_id: int,
    days_ahead: int = 30
) -> Dict[str, int]:
    """
    Sync calendar events from Google Calendar to database.
    
    Args:
        session: Database session
        user_id: User ID
        days_ahead: Number of days ahead to sync
    
    Returns:
        Dictionary with sync statistics
    """
    stats = {
        "created": 0,
        "updated": 0,
        "errors": 0
    }
    
    try:
        # Get events from Google Calendar
        time_min = datetime.utcnow()
        time_max = time_min + timedelta(days=days_ahead)
        
        events = await list_events(session, user_id, time_min, time_max)
        
        # Get existing events from database
        stmt = select(CalendarEvent).where(
            CalendarEvent.user_id == user_id
        )
        result = await session.execute(stmt)
        existing_events = {e.google_event_id: e for e in result.scalars().all()}
        
        # Process each event
        for event in events:
            event_id = event.get('id')
            if not event_id:
                continue
            
            try:
                if event_id in existing_events:
                    # Update existing
                    db_event = existing_events[event_id]
                    db_event.title = event.get('summary', 'No title')
                    db_event.description = event.get('description', '')
                    db_event.start_time = parse_event_time(event.get('start'))
                    db_event.end_time = parse_event_time(event.get('end'))
                    db_event.location = event.get('location', '')
                    db_event.attendees = event.get('attendees', [])
                    db_event.last_synced_at = datetime.utcnow()
                    stats["updated"] += 1
                else:
                    # Create new
                    db_event = CalendarEvent(
                        user_id=user_id,
                        google_event_id=event_id,
                        title=event.get('summary', 'No title'),
                        description=event.get('description', ''),
                        start_time=parse_event_time(event.get('start')),
                        end_time=parse_event_time(event.get('end')),
                        location=event.get('location', ''),
                        attendees=event.get('attendees', [])
                    )
                    session.add(db_event)
                    stats["created"] += 1
            except Exception as e:
                logger.error(f"Error processing event {event_id}: {e}")
                stats["errors"] += 1
        
        await session.commit()
        logger.info(f"Calendar sync completed for user {user_id}: {stats}")
        
    except Exception as e:
        logger.error(f"Error syncing calendar: {e}")
        stats["errors"] += 1
    
    return stats


def parse_event_time(time_str: Optional[str]) -> Optional[datetime]:
    """Parse event time string to datetime."""
    if not time_str:
        return None
    
    try:
        if 'T' in time_str:
            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        else:
            return datetime.fromisoformat(time_str)
    except Exception:
        return None

