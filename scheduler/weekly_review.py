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
    """Send weekly review to a user with adaptive learning insights."""
    try:
        # Get weekly stats
        stats = await get_weekly_stats(session, user.id)
        
        # Get readiness scores
        readiness = await calculate_readiness_scores(session, user.id)
        
        # Get adaptive learning insights
        from memory.adaptive_learning import (
            detect_recurring_patterns,
            adapt_behavior_from_patterns,
            suggest_automatic_flow
        )
        from memory.pattern_learning import get_user_habits
        
        adaptations = await adapt_behavior_from_patterns(session, user.id)
        habits = await get_user_habits(session, user.id)
        task_patterns = await detect_recurring_patterns(session, user.id, "task_creation")
        
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
        
        # Add adaptive learning insights
        if habits or task_patterns:
            message += "\n🧠 **What I've Learned This Week:**\n"
            
            if habits:
                for habit in habits[:2]:
                    if habit.pattern_type == "preferred_pillar":
                        data = habit.pattern_data or {}
                        pillar = data.get("preferred_pillar", "unknown")
                        message += f"• You prefer tasks in **{pillar.capitalize()}** category\n"
                    elif habit.pattern_type == "task_completion_time":
                        data = habit.pattern_data or {}
                        avg_minutes = data.get("average_minutes", 0)
                        hours = int(avg_minutes // 60)
                        minutes = int(avg_minutes % 60)
                        if hours > 0:
                            message += f"• Average task duration: **{hours}h {minutes}m**\n"
                        else:
                            message += f"• Average task duration: **{minutes}m**\n"
            
            if task_patterns:
                for pattern in task_patterns[:1]:
                    if pattern["type"] == "recurring_task":
                        message += (
                            f"• Recurring pattern detected: '{pattern['pattern']}' "
                            f"(every {pattern['frequency_days']:.0f} days)\n"
                        )
            
            # Check for automatic flow suggestions
            flow_suggestions = []
            for pattern in task_patterns:
                if pattern.get("confidence", 0) > 0.7:
                    suggestion = await suggest_automatic_flow(session, user.id, pattern)
                    if suggestion:
                        flow_suggestions.append(suggestion)
            
            if flow_suggestions:
                message += "\n💡 **Suggested Automation:**\n"
                message += f"{flow_suggestions[0]['description']}\n"
        
        message += "\n**This Week's Focus:**\n"
        message += "Let's plan your upcoming week. What would you like to prioritize?\n\n"
        message += "Use /insights to see more detailed adaptive learning insights."
        
        await application.bot.send_message(
            chat_id=user.telegram_id,
            text=message,
            parse_mode="Markdown"
        )
        
        logger.info(f"Sent weekly review to user {user.id}")
    except Exception as e:
        logger.error(f"Error sending review to user {user.id}: {e}", exc_info=True)

