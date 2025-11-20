"""
Deadline reminders job.
"""
import logging
from datetime import datetime, timedelta
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from tasks.priority_queue import get_upcoming_deadlines, get_overdue_tasks
from tasks.escalation import check_deadlines as escalate_task_deadlines, mark_overdue
from telegram_bot.bot import create_application

logger = logging.getLogger(__name__)


async def send_deadline_reminders():
    """Check and send deadline reminders."""
    async with AsyncSessionLocal() as session:
        # Get all active users
        stmt = select(User).where(
            User.is_active == True,
            User.is_onboarded == True
        )
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        # Get bot application
        application = create_application()
        
        for user in users:
            try:
                # Get upcoming deadlines (within 24 hours)
                deadlines = await get_upcoming_deadlines(session, user.id, days=1)
                
                if deadlines:
                    message = "⏰ **Deadline Reminders:**\n\n"
                    for task in deadlines[:5]:
                        due_str = task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else "No due date"
                        message += f"• {task.title} (due: {due_str})\n"
                    
                    await application.bot.send_message(
                        chat_id=user.telegram_id,
                        text=message,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error checking deadlines for user {user.id}: {e}")


async def escalate_deadlines():
    """Escalate approaching deadlines."""
    async with AsyncSessionLocal() as session:
        # Get all active users
        stmt = select(User).where(
            User.is_active == True,
            User.is_onboarded == True
        )
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        for user in users:
            try:
                # Check and escalate deadlines
                escalated = await escalate_task_deadlines(session, user.id)
                
                # Mark overdue
                overdue = await mark_overdue(session, user.id)
                
                if escalated or overdue:
                    # Get bot application
                    application = create_application()
                    
                    message = "🚨 **Priority Updates:**\n\n"
                    if escalated:
                        message += "Tasks escalated to urgent:\n"
                        for task in escalated:
                            message += f"• {task.title}\n"
                    
                    if overdue:
                        message += "\nOverdue tasks:\n"
                        for task in overdue[:5]:
                            message += f"• {task.title}\n"
                    
                    await application.bot.send_message(
                        chat_id=user.telegram_id,
                        text=message,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error escalating deadlines for user {user.id}: {e}")

