"""
Task scheduling to Google Calendar with conflict detection.
According to COMPREHENSIVE_PLAN.md and TESTING_AND_REFINEMENT_PLAN.md
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Task, User, CalendarEvent
from google_calendar.client import list_events, create_event, update_event, delete_event
from edge_cases.guardrails import check_user_autonomy

logger = logging.getLogger(__name__)


async def check_conflicts(
    session: AsyncSession,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_event_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Check for calendar conflicts in a time range.
    
    Args:
        session: Database session
        user_id: User ID
        start_time: Proposed start time
        end_time: Proposed end time
        exclude_event_id: Event ID to exclude from conflict check (for updates)
    
    Returns:
        List of conflicting events
    """
    try:
        # Get events in the time range
        events = await list_events(
            session=session,
            user_id=user_id,
            time_min=start_time - timedelta(hours=1),  # Check slightly before
            time_max=end_time + timedelta(hours=1),    # Check slightly after
            max_results=50
        )
        
        conflicts = []
        
        for event in events:
            # Skip excluded event (for updates)
            if exclude_event_id and event.get('id') == exclude_event_id:
                continue
            
            event_start_str = event.get('start')
            event_end_str = event.get('end')
            
            if not event_start_str or not event_end_str:
                continue
            
            try:
                # Parse event times
                if 'T' in event_start_str:
                    event_start = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))
                    event_end = datetime.fromisoformat(event_end_str.replace('Z', '+00:00'))
                else:
                    # All-day event
                    event_start = datetime.fromisoformat(event_start_str)
                    event_end = event_start + timedelta(days=1)
                
                # Remove timezone for comparison
                if event_start.tzinfo:
                    event_start = event_start.replace(tzinfo=None)
                if event_end.tzinfo:
                    event_end = event_end.replace(tzinfo=None)
                
                # Check for overlap
                # Conflict if: proposed_start < event_end AND proposed_end > event_start
                if start_time < event_end and end_time > event_start:
                    conflicts.append({
                        'id': event.get('id'),
                        'summary': event.get('summary', 'No title'),
                        'start': event_start_str,
                        'end': event_end_str,
                        'location': event.get('location', '')
                    })
            except Exception as e:
                logger.warning(f"Error parsing event time for conflict check: {e}")
                continue
        
        return conflicts
        
    except Exception as e:
        logger.error(f"Error checking conflicts: {e}")
        return []


async def suggest_time_slots(
    session: AsyncSession,
    user_id: int,
    duration_minutes: int,
    preferred_date: Optional[datetime] = None,
    preferred_time_of_day: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Suggest optimal time slots for scheduling a task.
    
    Args:
        session: Database session
        user_id: User ID
        duration_minutes: Task duration in minutes
        preferred_date: Preferred date (default: today)
        preferred_time_of_day: "morning", "afternoon", "evening" (optional)
    
    Returns:
        List of suggested time slots with:
        - start_time: datetime
        - end_time: datetime
        - conflicts: int (number of conflicts)
        - quality_score: float (0-1)
    """
    try:
        # Get user's work hours
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return []
        
        work_start_hour = user.work_start_hour or 8
        work_end_hour = user.work_end_hour or 20
        
        # Determine search date range
        if preferred_date:
            search_date = preferred_date.date()
        else:
            search_date = datetime.utcnow().date()
        
        # Get events for the next 3 days starting from preferred date
        time_min = datetime.combine(search_date, datetime.min.time())
        time_max = time_min + timedelta(days=3)
        
        events = await list_events(
            session=session,
            user_id=user_id,
            time_min=time_min,
            time_max=time_max,
            max_results=50
        )
        
        # Parse events into time blocks
        event_blocks = []
        for event in events:
            event_start_str = event.get('start')
            event_end_str = event.get('end')
            
            if not event_start_str or not event_end_str:
                continue
            
            try:
                if 'T' in event_start_str:
                    event_start = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))
                    event_end = datetime.fromisoformat(event_end_str.replace('Z', '+00:00'))
                    if event_start.tzinfo:
                        event_start = event_start.replace(tzinfo=None)
                    if event_end.tzinfo:
                        event_end = event_end.replace(tzinfo=None)
                    
                    # Only consider events on search date or later
                    if event_start.date() >= search_date:
                        event_blocks.append((event_start, event_end))
            except Exception as e:
                logger.warning(f"Error parsing event for suggestions: {e}")
                continue
        
        # Sort events by start time
        event_blocks.sort(key=lambda x: x[0])
        
        # Generate suggestions
        suggestions = []
        now = datetime.utcnow()
        
        # Check each day for available slots
        for day_offset in range(3):
            check_date = search_date + timedelta(days=day_offset)
            
            # Start from work start hour or now if today
            day_start = datetime.combine(check_date, datetime.min.time()).replace(
                hour=work_start_hour, minute=0
            )
            if check_date == now.date() and day_start < now:
                day_start = now.replace(minute=0, second=0, microsecond=0)
            
            day_end = datetime.combine(check_date, datetime.min.time()).replace(
                hour=work_end_hour, minute=0
            )
            
            # Filter events for this day
            day_events = [
                (start, end) for start, end in event_blocks
                if start.date() == check_date
            ]
            
            # Find free slots
            free_slots = []
            current_time = day_start
            
            for event_start, event_end in day_events:
                if current_time < event_start:
                    # Free slot before this event
                    slot_end = min(event_start, day_end)
                    if (slot_end - current_time).total_seconds() >= duration_minutes * 60:
                        free_slots.append((current_time, slot_end))
                current_time = max(current_time, event_end)
            
            # Check for slot after last event
            if current_time < day_end:
                slot_end = day_end
                if (slot_end - current_time).total_seconds() >= duration_minutes * 60:
                    free_slots.append((current_time, slot_end))
            
            # Generate suggestions from free slots
            for slot_start, slot_end in free_slots:
                # Suggest slot at the beginning of free time
                suggested_start = slot_start
                suggested_end = suggested_start + timedelta(minutes=duration_minutes)
                
                # Check if it fits
                if suggested_end <= slot_end and suggested_end <= day_end:
                    # Calculate quality score (prefer earlier, prefer today if preferred_date is today)
                    quality_score = 1.0
                    
                    # Prefer earlier days
                    quality_score -= day_offset * 0.2
                    
                    # Prefer preferred time of day if specified
                    hour = suggested_start.hour
                    if preferred_time_of_day == "morning" and 8 <= hour < 12:
                        quality_score += 0.3
                    elif preferred_time_of_day == "afternoon" and 12 <= hour < 17:
                        quality_score += 0.3
                    elif preferred_time_of_day == "evening" and 17 <= hour < 20:
                        quality_score += 0.3
                    
                    # Prefer slots starting at :00 or :30
                    if suggested_start.minute in [0, 30]:
                        quality_score += 0.1
                    
                    suggestions.append({
                        'start_time': suggested_start,
                        'end_time': suggested_end,
                        'conflicts': 0,  # Already checked, no conflicts
                        'quality_score': min(quality_score, 1.0),
                        'time_of_day': get_time_of_day_label(suggested_start.hour)
                    })
        
        # Sort by quality score (best first)
        suggestions.sort(key=lambda x: x['quality_score'], reverse=True)
        
        # Return top 5 suggestions
        return suggestions[:5]
        
    except Exception as e:
        logger.error(f"Error suggesting time slots: {e}")
        return []


def get_time_of_day_label(hour: int) -> str:
    """Get time of day label from hour."""
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


async def schedule_task_to_calendar(
    session: AsyncSession,
    user_id: int,
    task_id: int,
    start_time: datetime,
    end_time: Optional[datetime] = None,
    description: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Schedule a task to Google Calendar with conflict checking and guardrails.
    
    Args:
        session: Database session
        user_id: User ID
        task_id: Task ID
        start_time: Start time
        end_time: End time (optional, calculated from task if not provided)
        description: Event description (optional)
    
    Returns:
        Tuple of (success, event_id, error_message)
    """
    try:
        # Check guardrails - scheduling requires confirmation
        autonomy_check = await check_user_autonomy("schedule_task", requires_confirmation=False)
        if not autonomy_check["allowed"]:
            return False, None, "Scheduling is not allowed at this time."
        
        # Get task
        from tasks.service import get_task
        task = await get_task(session, task_id, user_id)
        
        if not task:
            return False, None, "Task not found."
        
        # Check if user is connected to Google Calendar
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.google_calendar_connected:
            return False, None, "Google Calendar is not connected. Please connect your calendar first."
        
        # Calculate end time if not provided
        if end_time is None:
            if task.estimated_duration:
                end_time = start_time + timedelta(minutes=task.estimated_duration)
            else:
                end_time = start_time + timedelta(hours=1)  # Default 1 hour
        
        # Validate time range
        if end_time <= start_time:
            return False, None, "End time must be after start time."
        
        if start_time < datetime.utcnow():
            return False, None, "Cannot schedule tasks in the past."
        
        # Check for conflicts (exclude existing calendar event if updating)
        conflicts = await check_conflicts(
            session,
            user_id,
            start_time,
            end_time,
            exclude_event_id=task.calendar_event_id
        )
        
        if conflicts:
            conflict_summary = ", ".join([c['summary'] for c in conflicts[:3]])
            return False, None, f"Time slot conflicts with: {conflict_summary}"
        
        # Delete existing calendar event if task already has one (for rescheduling)
        if task.calendar_event_id:
            try:
                await delete_event(session, user_id, task.calendar_event_id)
                logger.info(f"Deleted existing calendar event {task.calendar_event_id} for task {task_id}")
            except Exception as e:
                logger.warning(f"Could not delete existing calendar event: {e}")
                # Continue anyway
        
        # Create calendar event
        event_title = f"📋 {task.title}"
        event_description = description or task.description or f"Task: {task.title}"
        
        if task.priority:
            event_description = f"[Priority: {task.priority.value.capitalize()}] {event_description}"
        
        created_event = await create_event(
            session=session,
            user_id=user_id,
            title=event_title,
            start_time=start_time,
            end_time=end_time,
            description=event_description
        )
        
        event_id = created_event['id']
        
        # Update task with scheduling info
        task.scheduled_start = start_time
        task.scheduled_end = end_time
        task.calendar_event_id = event_id
        await session.flush()
        
        # Link calendar event to task
        stmt = select(CalendarEvent).where(CalendarEvent.google_event_id == event_id)
        result = await session.execute(stmt)
        calendar_event = result.scalar_one_or_none()
        
        if calendar_event:
            calendar_event.linked_task_id = task_id
            await session.flush()
        
        logger.info(f"Scheduled task {task_id} to calendar as event {event_id}")
        return True, event_id, None
        
    except Exception as e:
        logger.error(f"Error scheduling task to calendar: {e}")
        return False, None, f"Error scheduling task: {str(e)}"


async def unschedule_task_from_calendar(
    session: AsyncSession,
    user_id: int,
    task_id: int
) -> Tuple[bool, Optional[str]]:
    """
    Remove task from Google Calendar.
    
    Args:
        session: Database session
        user_id: User ID
        task_id: Task ID
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Get task
        from tasks.service import get_task
        task = await get_task(session, task_id, user_id)
        
        if not task:
            return False, "Task not found."
        
        if not task.calendar_event_id:
            return False, "Task is not scheduled to calendar."
        
        # Delete calendar event
        try:
            await delete_event(session, user_id, task.calendar_event_id)
        except Exception as e:
            logger.warning(f"Could not delete calendar event: {e}")
            # Continue to clean up task anyway
        
        # Clear scheduling info from task
        task.scheduled_start = None
        task.scheduled_end = None
        task.calendar_event_id = None
        await session.flush()
        
        logger.info(f"Unscheduled task {task_id} from calendar")
        return True, None
        
    except Exception as e:
        logger.error(f"Error unscheduling task from calendar: {e}")
        return False, f"Error unscheduling task: {str(e)}"

