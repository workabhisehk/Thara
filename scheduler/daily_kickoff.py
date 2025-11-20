"""
Daily kickoff summary job.
"""
import logging
from datetime import datetime, timedelta
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from calendar.client import list_events
from tasks.priority_queue import get_priority_queue, get_upcoming_deadlines
from telegram_bot.bot import create_application

logger = logging.getLogger(__name__)


async def send_daily_summaries():
    """Send daily kickoff summaries to all active users."""
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
                # Check if it's a workday and within work hours
                now = datetime.utcnow()
                work_start = now.replace(hour=user.work_start_hour, minute=0, second=0, microsecond=0)
                
                # Only send if it's around work start time (within 1 hour)
                if abs((now - work_start).total_seconds()) > 3600:
                    continue
                
                await send_user_summary(session, user, application)
            except Exception as e:
                logger.error(f"Error sending daily summary to user {user.id}: {e}")


async def send_user_summary(session, user, application):
    """Send daily summary to a user."""
    try:
        # Get today's calendar events
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        events = []
        if user.google_calendar_connected:
            try:
                events = await list_events(session, user.id, today_start, today_end, max_results=20)
            except Exception as e:
                logger.error(f"Error getting calendar events: {e}")
        
        # Get priority tasks
        tasks = await get_priority_queue(session, user.id, limit=10)
        
        # Get upcoming deadlines
        deadlines = await get_upcoming_deadlines(session, user.id, days=3)
        
        # Format message
        message = f"🌅 **Good Morning!**\n\n"
        message += f"**Today's Calendar:**\n"
        if events:
            for event in events[:5]:
                start_time = event.get('start', '')
                message += f"• {event.get('summary')} at {start_time}\n"
        else:
            message += "No events scheduled.\n"
        
        message += f"\n**Priority Tasks:**\n"
        if tasks:
            for i, task in enumerate(tasks[:5], 1):
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority.value, "⚪")
                message += f"{i}. {priority_emoji} {task.title}\n"
        else:
            message += "No active tasks.\n"
        
        if deadlines:
            message += f"\n**Upcoming Deadlines:**\n"
            for deadline in deadlines[:3]:
                due_str = deadline.due_date.strftime('%Y-%m-%d') if deadline.due_date else "No due date"
                message += f"• {deadline.title} (due: {due_str})\n"
        
        # Send via Telegram
        await application.bot.send_message(
            chat_id=user.telegram_id,
            text=message,
            parse_mode="Markdown"
        )
        
        logger.info(f"Sent daily summary to user {user.id}")
    except Exception as e:
        logger.error(f"Error sending summary to user {user.id}: {e}")

