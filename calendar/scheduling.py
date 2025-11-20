"""
Scheduling logic for tasks and events.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from calendar.conflict_detection import detect_conflicts, find_available_slots
from calendar.client import create_event
from database.models import User, Task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def schedule_task(
    session: AsyncSession,
    user_id: int,
    task_id: int,
    preferred_time: Optional[datetime] = None,
    duration_minutes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Schedule a task in calendar.
    
    Args:
        session: Database session
        user_id: User ID
        task_id: Task ID
        preferred_time: Preferred start time (optional)
        duration_minutes: Duration in minutes (optional)
    
    Returns:
        Dictionary with scheduling result
    """
    # Get task
    stmt = select(Task).where(
        Task.id == task_id,
        Task.user_id == user_id
    )
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise ValueError("Task not found")
    
    # Get user
    user_stmt = select(User).where(User.id == user_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise ValueError("User not found")
    
    # Determine duration
    if not duration_minutes:
        duration_minutes = task.estimated_duration or 60  # Default 1 hour
    
    # Determine time window
    if preferred_time:
        start_date = preferred_time
        end_date = preferred_time + timedelta(days=7)
    elif task.due_date:
        start_date = datetime.utcnow()
        end_date = task.due_date
    else:
        start_date = datetime.utcnow()
        end_date = datetime.utcnow() + timedelta(days=7)
    
    # Find available slots
    slots = await find_available_slots(
        session,
        user_id,
        duration_minutes,
        start_date,
        end_date,
        user.work_start_hour,
        user.work_end_hour
    )
    
    if not slots:
        return {
            "success": False,
            "message": "No available time slots found",
            "slots": []
        }
    
    # Use first available slot
    slot_start, slot_end = slots[0]
    
    # Check for conflicts
    conflicts = await detect_conflicts(session, user_id, slot_start, slot_end)
    
    if conflicts:
        # Try next slot
        if len(slots) > 1:
            slot_start, slot_end = slots[1]
            conflicts = await detect_conflicts(session, user_id, slot_start, slot_end)
        
        if conflicts:
            return {
                "success": False,
                "message": "All suggested slots have conflicts",
                "slots": slots,
                "conflicts": conflicts
            }
    
    # Create calendar event
    try:
        event = await create_event(
            session,
            user_id,
            task.title,
            slot_start,
            slot_end,
            description=task.description or f"Task: {task.title}"
        )
        
        # Update task
        task.scheduled_start = slot_start
        task.scheduled_end = slot_end
        task.calendar_event_id = event['id']
        await session.flush()
        
        return {
            "success": True,
            "event": event,
            "scheduled_start": slot_start.isoformat(),
            "scheduled_end": slot_end.isoformat(),
            "alternative_slots": slots[1:5]  # Show alternatives
        }
    except Exception as e:
        logger.error(f"Error scheduling task: {e}")
        return {
            "success": False,
            "message": f"Error creating calendar event: {str(e)}",
            "slots": slots
        }

