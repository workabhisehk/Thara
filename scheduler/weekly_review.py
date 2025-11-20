"""
Weekly review job.
"""
import logging
from datetime import datetime, timedelta
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from analytics.completion_tracking import get_weekly_stats
from analytics.readiness_forecasting import calculate_readiness_scores
from telegram_bot.bot import create_application

logger = logging.getLogger(__name__)


async def send_weekly_review():
    """Send weekly reviews to all active users."""
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
                await send_user_review(session, user, application)
            except Exception as e:
                logger.error(f"Error sending weekly review to user {user.id}: {e}")


async def send_user_review(session, user, application):
    """Send weekly review to a user."""
    try:
        # Get weekly stats
        stats = await get_weekly_stats(session, user.id)
        
        # Get readiness scores
        readiness = await calculate_readiness_scores(session, user.id)
        
        # Format message
        message = "📊 **Weekly Review**\n\n"
        
        message += "**Last Week's Performance:**\n"
        message += f"• Tasks completed: {stats.get('completed', 0)}\n"
        message += f"• Tasks created: {stats.get('created', 0)}\n"
        message += f"• Overdue tasks: {stats.get('overdue', 0)}\n"
        message += f"• Completion rate: {stats.get('completion_rate', 0):.1f}%\n"
        
        if readiness:
            message += "\n**Upcoming Deadlines Readiness:**\n"
            for item in readiness[:3]:
                message += f"• {item.get('task_title')}: {item.get('readiness_score', 0):.0f}% ready\n"
        
        message += "\n**This Week's Focus:**\n"
        message += "Let's plan your upcoming week. What would you like to prioritize?"
        
        await application.bot.send_message(
            chat_id=user.telegram_id,
            text=message,
            parse_mode="Markdown"
        )
        
        logger.info(f"Sent weekly review to user {user.id}")
    except Exception as e:
        logger.error(f"Error sending review to user {user.id}: {e}")

