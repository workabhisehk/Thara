"""
Google Calendar API client for event operations.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError
from calendar.auth import get_user_credentials, get_calendar_service
from database.models import CalendarEvent, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def list_events(
    session: AsyncSession,
    user_id: int,
    time_min: Optional[datetime] = None,
    time_max: Optional[datetime] = None,
    max_results: int = 50
) -> List[Dict[str, Any]]:
    """
    List calendar events for user.
    
    Args:
        session: Database session
        user_id: User ID
        time_min: Start time (default: now)
        time_max: End time (default: 7 days from now)
        max_results: Maximum number of results
    
    Returns:
        List of event dictionaries
    """
    credentials = await get_user_credentials(session, user_id)
    if not credentials:
        raise ValueError("User not connected to Google Calendar")
    
    service = get_calendar_service(credentials)
    
    if time_min is None:
        time_min = datetime.utcnow()
    if time_max is None:
        time_max = time_min + timedelta(days=7)
    
    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min.isoformat() + 'Z',
            timeMax=time_max.isoformat() + 'Z',
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        return [
            {
                'id': event.get('id'),
                'summary': event.get('summary', 'No title'),
                'description': event.get('description', ''),
                'start': event.get('start', {}).get('dateTime') or event.get('start', {}).get('date'),
                'end': event.get('end', {}).get('dateTime') or event.get('end', {}).get('date'),
                'location': event.get('location', ''),
                'attendees': [a.get('email') for a in event.get('attendees', [])],
                'recurringEventId': event.get('recurringEventId'),
            }
            for event in events
        ]
    except HttpError as e:
        logger.error(f"Error listing events: {e}")
        raise


async def create_event(
    session: AsyncSession,
    user_id: int,
    title: str,
    start_time: datetime,
    end_time: datetime,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a calendar event.
    
    Args:
        session: Database session
        user_id: User ID
        title: Event title
        start_time: Start datetime
        end_time: End datetime
        description: Event description
        location: Event location
        attendees: List of attendee emails
    
    Returns:
        Created event dictionary
    """
    credentials = await get_user_credentials(session, user_id)
    if not credentials:
        raise ValueError("User not connected to Google Calendar")
    
    service = get_calendar_service(credentials)
    
    event = {
        'summary': title,
        'description': description or '',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'UTC',
        },
    }
    
    if location:
        event['location'] = location
    
    if attendees:
        event['attendees'] = [{'email': email} for email in attendees]
    
    try:
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        # Store in database
        db_event = CalendarEvent(
            user_id=user_id,
            google_event_id=created_event['id'],
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location=location,
            attendees=attendees or []
        )
        session.add(db_event)
        await session.flush()
        
        return {
            'id': created_event['id'],
            'summary': created_event.get('summary'),
            'start': created_event.get('start', {}).get('dateTime'),
            'end': created_event.get('end', {}).get('dateTime'),
        }
    except HttpError as e:
        logger.error(f"Error creating event: {e}")
        raise


async def update_event(
    session: AsyncSession,
    user_id: int,
    event_id: str,
    title: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update a calendar event.
    
    Args:
        session: Database session
        user_id: User ID
        event_id: Google Calendar event ID
        title: New title (optional)
        start_time: New start time (optional)
        end_time: New end time (optional)
        description: New description (optional)
    
    Returns:
        Updated event dictionary
    """
    credentials = await get_user_credentials(session, user_id)
    if not credentials:
        raise ValueError("User not connected to Google Calendar")
    
    service = get_calendar_service(credentials)
    
    try:
        # Get existing event
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        # Update fields
        if title:
            event['summary'] = title
        if start_time:
            event['start'] = {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            }
        if end_time:
            event['end'] = {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            }
        if description is not None:
            event['description'] = description
        
        # Update event
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event
        ).execute()
        
        # Update in database
        stmt = select(CalendarEvent).where(
            CalendarEvent.google_event_id == event_id,
            CalendarEvent.user_id == user_id
        )
        result = await session.execute(stmt)
        db_event = result.scalar_one_or_none()
        
        if db_event:
            if title:
                db_event.title = title
            if start_time:
                db_event.start_time = start_time
            if end_time:
                db_event.end_time = end_time
            if description is not None:
                db_event.description = description
            db_event.last_synced_at = datetime.utcnow()
            await session.flush()
        
        return {
            'id': updated_event['id'],
            'summary': updated_event.get('summary'),
            'start': updated_event.get('start', {}).get('dateTime'),
            'end': updated_event.get('end', {}).get('dateTime'),
        }
    except HttpError as e:
        logger.error(f"Error updating event: {e}")
        raise


async def delete_event(
    session: AsyncSession,
    user_id: int,
    event_id: str
) -> bool:
    """
    Delete a calendar event.
    
    Args:
        session: Database session
        user_id: User ID
        event_id: Google Calendar event ID
    
    Returns:
        True if successful
    """
    credentials = await get_user_credentials(session, user_id)
    if not credentials:
        raise ValueError("User not connected to Google Calendar")
    
    service = get_calendar_service(credentials)
    
    try:
        service.events().delete(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        # Delete from database
        stmt = select(CalendarEvent).where(
            CalendarEvent.google_event_id == event_id,
            CalendarEvent.user_id == user_id
        )
        result = await session.execute(stmt)
        db_event = result.scalar_one_or_none()
        
        if db_event:
            await session.delete(db_event)
            await session.flush()
        
        return True
    except HttpError as e:
        logger.error(f"Error deleting event: {e}")
        raise

