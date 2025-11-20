"""
Time-based reminders based on estimated completion time.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from database.models import Task, TaskStatus, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from telegram_bot.bot import create_application

logger = logging.getLogger(__name__)


async def calculate_reminder_time(
    task: Task,
    buffer_hours: float = 2.0
) -> Optional[datetime]:
    """
    Calculate when to remind user to start a task.
    
    Formula: reminder_time = due_date - estimated_duration - buffer
    
    Args:
        task: Task object
        buffer_hours: Buffer time in hours before deadline
    
    Returns:
        Datetime when reminder should be sent, or None if not applicable
    """
    if not task.due_date or not task.estimated_duration:
        return None
    
    # Convert estimated duration to hours
    estimated_hours = task.estimated_duration / 60.0
    
    # Calculate reminder time
    reminder_time = task.due_date - timedelta(hours=estimated_hours + buffer_hours)
    
    # Don't remind if reminder time is in the past
    if reminder_time < datetime.utcnow():
        return None
    
    return reminder_time


async def get_tasks_needing_reminders(
    session: AsyncSession,
    user_id: int,
    check_window_hours: int = 2
) -> List[Dict[str, Any]]:
    """
    Get tasks that need reminders based on estimated completion time.
    
    Args:
        session: Database session
        user_id: User ID
        check_window_hours: Check for reminders within this window
    
    Returns:
        List of tasks with reminder information
    """
    now = datetime.utcnow()
    window_end = now + timedelta(hours=check_window_hours)
    
    # Get active tasks with due dates and estimated durations
    stmt = select(Task).where(
        and_(
            Task.user_id == user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            Task.due_date.isnot(None),
            Task.estimated_duration.isnot(None),
            Task.scheduled_start.is_(None)  # Not yet scheduled
        )
    )
    
    result = await session.execute(stmt)
    tasks = result.scalars().all()
    
    reminders = []
    for task in tasks:
        reminder_time = await calculate_reminder_time(task)
        
        if reminder_time and now <= reminder_time <= window_end:
            # Calculate urgency
            time_until_deadline = (task.due_date - now).total_seconds() / 3600
            estimated_hours = task.estimated_duration / 60.0
            
            urgency = "high" if time_until_deadline < estimated_hours * 1.5 else "medium"
            
            reminders.append({
                "task": task,
                "reminder_time": reminder_time,
                "time_until_deadline_hours": time_until_deadline,
                "estimated_hours": estimated_hours,
                "urgency": urgency
            })
    
    return reminders


async def send_time_based_reminders(session: AsyncSession, user_id: int):
    """
    Send reminders for tasks based on estimated completion time.
    
    Args:
        session: Database session
        user_id: User ID
    """
    reminders = await get_tasks_needing_reminders(session, user_id)
    
    if not reminders:
        return
    
    # Get user
    user = await session.get(User, user_id)
    if not user:
        return
    
    # Get bot application
    application = create_application()
    
    for reminder in reminders:
        task = reminder["task"]
        time_until_deadline = reminder["time_until_deadline_hours"]
        estimated_hours = reminder["estimated_hours"]
        urgency = reminder["urgency"]
        
        # Format message
        urgency_emoji = "🚨" if urgency == "high" else "⏰"
        
        message = f"{urgency_emoji} **Time to Start Task**\n\n"
        message += f"**{task.title}**\n\n"
        message += f"⏱ Estimated duration: {estimated_hours:.1f} hours\n"
        message += f"📅 Due in: {time_until_deadline:.1f} hours\n\n"
        
        if urgency == "high":
            message += "⚠️ This task needs to be started soon to meet the deadline!\n\n"
        else:
            message += "💡 Consider starting this task soon to ensure timely completion.\n\n"
        
        message += "Would you like me to schedule time for this task?"
        
        try:
            await application.bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode="Markdown"
            )
            
            logger.info(f"Sent time-based reminder for task {task.id} to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending reminder: {e}")


async def confirm_estimated_time(
    session: AsyncSession,
    user_id: int,
    task_id: int,
    estimated_minutes: int
) -> bool:
    """
    Confirm and update estimated time for a task.
    
    Args:
        session: Database session
        user_id: User ID
        task_id: Task ID
        estimated_minutes: Estimated duration in minutes
    
    Returns:
        True if successful
    """
    task = await session.get(Task, task_id)
    if not task or task.user_id != user_id:
        return False
    
    task.estimated_duration = estimated_minutes
    await session.flush()
    
    logger.info(f"Updated estimated time for task {task_id}: {estimated_minutes} minutes")
    return True

