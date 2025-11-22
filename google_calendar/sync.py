"""
Calendar synchronization with bidirectional task linking.
According to COMPREHENSIVE_PLAN.md and Calendar Integration requirements.
"""
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from google_calendar.client import list_events
from google_calendar.auth import get_user_credentials
from database.models import CalendarEvent, User, Task, TaskStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

logger = logging.getLogger(__name__)


async def sync_calendar(
    session: AsyncSession,
    user_id: int,
    days_ahead: int = 30
) -> Dict[str, int]:
    """
    Sync calendar events from Google Calendar to database with bidirectional task linking.
    
    This function:
    1. Syncs calendar events from Google Calendar to database
    2. Updates task scheduled times when calendar events change
    3. Links calendar events to tasks when calendar_event_id matches
    4. Suggests linking for similar events/tasks
    
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
        "linked": 0,
        "task_updated": 0,
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
        
        # Get tasks with calendar_event_id to maintain links
        tasks_stmt = select(Task).where(
            and_(
                Task.user_id == user_id,
                Task.calendar_event_id.isnot(None)
            )
        )
        tasks_result = await session.execute(tasks_stmt)
        tasks_by_event_id = {t.calendar_event_id: t for t in tasks_result.scalars().all()}
        
        # Process each event
        for event in events:
            event_id = event.get('id')
            if not event_id:
                continue
            
            try:
                start_time = parse_event_time(event.get('start'))
                end_time = parse_event_time(event.get('end'))
                
                if event_id in existing_events:
                    # Update existing event
                    db_event = existing_events[event_id]
                    old_start = db_event.start_time
                    old_end = db_event.end_time
                    
                    db_event.title = event.get('summary', 'No title')
                    db_event.description = event.get('description', '')
                    db_event.start_time = start_time
                    db_event.end_time = end_time
                    db_event.location = event.get('location', '')
                    db_event.attendees = event.get('attendees', [])
                    db_event.last_synced_at = datetime.utcnow()
                    stats["updated"] += 1
                    
                    # Update linked task if times changed
                    if db_event.linked_task_id and (old_start != start_time or old_end != end_time):
                        task = tasks_by_event_id.get(event_id)
                        if task:
                            task.scheduled_start = start_time
                            task.scheduled_end = end_time
                            stats["task_updated"] += 1
                            logger.info(f"Updated task {task.id} scheduled times from calendar event {event_id}")
                    
                    # Ensure task link is maintained
                    if event_id in tasks_by_event_id:
                        task = tasks_by_event_id[event_id]
                        if db_event.linked_task_id != task.id:
                            db_event.linked_task_id = task.id
                            stats["linked"] += 1
                else:
                    # Create new event
                    linked_task_id = None
                    
                    # Check if this event is linked to a task
                    if event_id in tasks_by_event_id:
                        linked_task_id = tasks_by_event_id[event_id].id
                        stats["linked"] += 1
                    
                    db_event = CalendarEvent(
                        user_id=user_id,
                        google_event_id=event_id,
                        title=event.get('summary', 'No title'),
                        description=event.get('description', ''),
                        start_time=start_time,
                        end_time=end_time,
                        location=event.get('location', ''),
                        attendees=event.get('attendees', []),
                        linked_task_id=linked_task_id
                    )
                    session.add(db_event)
                    stats["created"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing event {event_id}: {e}")
                stats["errors"] += 1
        
        # Clean up orphaned links (events deleted from calendar but still linked)
        await _cleanup_orphaned_links(session, user_id, events, stats)
        
        await session.commit()
        logger.info(f"Calendar sync completed for user {user_id}: {stats}")
        
    except Exception as e:
        logger.error(f"Error syncing calendar: {e}")
        stats["errors"] += 1
    
    return stats


async def _cleanup_orphaned_links(
    session: AsyncSession,
    user_id: int,
    current_events: List[Dict],
    stats: Dict[str, int]
) -> None:
    """Clean up tasks that reference calendar events that no longer exist."""
    try:
        # Get event IDs from current sync
        current_event_ids = {e.get('id') for e in current_events if e.get('id')}
        
        # Find tasks with calendar_event_id that don't exist in current events
        tasks_stmt = select(Task).where(
            and_(
                Task.user_id == user_id,
                Task.calendar_event_id.isnot(None),
                ~Task.calendar_event_id.in_(current_event_ids) if current_event_ids else False
            )
        )
        tasks_result = await session.execute(tasks_stmt)
        orphaned_tasks = tasks_result.scalars().all()
        
        for task in orphaned_tasks:
            # Don't auto-clear if event was scheduled recently (might be temporary sync issue)
            if task.scheduled_start and task.scheduled_start > datetime.utcnow() - timedelta(days=1):
                logger.warning(f"Task {task.id} references missing calendar event {task.calendar_event_id}, but scheduled recently - keeping link")
                continue
            
            logger.info(f"Clearing orphaned calendar link for task {task.id} (event {task.calendar_event_id} not found)")
            task.calendar_event_id = None
            task.scheduled_start = None
            task.scheduled_end = None
            
    except Exception as e:
        logger.error(f"Error cleaning up orphaned links: {e}")


async def suggest_event_task_links(
    session: AsyncSession,
    user_id: int,
    days_ahead: int = 7
) -> List[Dict[str, any]]:
    """
    Suggest linking calendar events to tasks based on similarity.
    
    Args:
        session: Database session
        user_id: User ID
        days_ahead: Number of days ahead to check
    
    Returns:
        List of suggested links with:
        - event_id: Calendar event ID
        - event_title: Event title
        - event_time: Event start time
        - task_id: Task ID
        - task_title: Task title
        - similarity_score: float (0-1)
        - reason: str (why they might be linked)
    """
    suggestions = []
    
    try:
        # Get upcoming events
        time_min = datetime.utcnow()
        time_max = time_min + timedelta(days=days_ahead)
        events = await list_events(session, user_id, time_min, time_max)
        
        # Get tasks without calendar links
        tasks_stmt = select(Task).where(
            and_(
                Task.user_id == user_id,
                Task.calendar_event_id.is_(None),
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])  # Only active tasks
            )
        )
        tasks_result = await session.execute(tasks_stmt)
        unlinked_tasks = tasks_result.scalars().all()
        
        # Get existing calendar events from DB to exclude already linked ones
        events_stmt = select(CalendarEvent).where(
            and_(
                CalendarEvent.user_id == user_id,
                CalendarEvent.linked_task_id.is_(None)
            )
        )
        events_result = await session.execute(events_stmt)
        unlinked_events = {e.google_event_id: e for e in events_result.scalars().all()}
        
        # Simple similarity matching based on title and timing
        for event in events:
            event_id = event.get('id')
            if not event_id or event_id not in unlinked_events:
                continue
            
            event_title = event.get('summary', '').lower()
            event_start = parse_event_time(event.get('start'))
            
            if not event_start:
                continue
            
            for task in unlinked_tasks:
                task_title = task.title.lower()
                
                # Calculate similarity score
                similarity = 0.0
                reasons = []
                
                # Title similarity (simple word overlap)
                event_words = set(event_title.split())
                task_words = set(task_title.split())
                
                if event_words and task_words:
                    overlap = len(event_words & task_words)
                    total_words = len(event_words | task_words)
                    word_similarity = overlap / total_words if total_words > 0 else 0
                    
                    if word_similarity > 0.3:
                        similarity += word_similarity * 0.6
                        reasons.append(f"Title similarity: {word_similarity:.0%}")
                
                # Time proximity to due date
                if task.due_date:
                    time_diff = abs((event_start - task.due_date).total_seconds())
                    if time_diff < 3600:  # Within 1 hour
                        similarity += 0.3
                        reasons.append("Time matches due date")
                    elif time_diff < 86400:  # Within 1 day
                        similarity += 0.1
                        reasons.append("Time near due date")
                
                # Scheduled time proximity
                if task.scheduled_start:
                    time_diff = abs((event_start - task.scheduled_start).total_seconds())
                    if time_diff < 3600:  # Within 1 hour
                        similarity += 0.4
                        reasons.append("Time matches scheduled time")
                
                # Only suggest if similarity is significant
                if similarity > 0.4:
                    suggestions.append({
                        "event_id": event_id,
                        "event_title": event.get('summary', 'No title'),
                        "event_time": event_start,
                        "task_id": task.id,
                        "task_title": task.title,
                        "similarity_score": min(similarity, 1.0),
                        "reason": "; ".join(reasons) if reasons else "Potential match"
                    })
        
        # Sort by similarity score (highest first)
        suggestions.sort(key=lambda x: x['similarity_score'], reverse=True)
        
    except Exception as e:
        logger.error(f"Error suggesting event-task links: {e}")
    
    return suggestions[:10]  # Return top 10 suggestions


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

