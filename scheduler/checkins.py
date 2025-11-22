"""
30-minute check-in job.
"""
import logging
from datetime import datetime
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from clarifications.queue import get_pending_clarifications
from ai.prompts import CHECKIN_PROMPT
from ai.langchain_setup import get_llm
from telegram_bot.bot import create_application

logger = logging.getLogger(__name__)


async def send_check_ins():
    """Send check-ins to active users."""
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
                # Check if within work hours
                now = datetime.utcnow()
                hour = now.hour
                
                if not (user.work_start_hour <= hour < user.work_end_hour):
                    continue
                
                # Use adaptive check-in timing if available
                from memory.adaptive_learning import adapt_behavior_from_patterns
                adaptations = await adapt_behavior_from_patterns(session, user.id)
                
                # If we have learned a preferred check-in time, only send at that hour
                if adaptations.get("check_in_timing"):
                    preferred_hour = adaptations["check_in_timing"]["suggested_hour"]
                    confidence = adaptations["check_in_timing"]["confidence"]
                    
                    # Only use adaptive timing if confidence is high enough
                    if confidence >= 0.6 and hour != preferred_hour:
                        # Skip this check-in if not at preferred time
                        continue
                
                await send_user_check_in(session, user, application)
            except Exception as e:
                logger.error(f"Error sending check-in to user {user.id}: {e}")


async def send_user_check_in(session, user, application):
    """Send check-in to a user."""
    try:
        # Get pending clarifications
        clarifications = await get_pending_clarifications(session, user.id, limit=1)
        
        if clarifications:
            # Ask clarification question
            clarification = clarifications[0]
            message = f"❓ {clarification.question}"
            await application.bot.send_message(
                chat_id=user.telegram_id,
                text=message
            )
            return
        
        # Generate contextual check-in
        from tasks.priority_queue import get_priority_queue, get_upcoming_deadlines
        
        active_tasks = await get_priority_queue(session, user.id, limit=5)
        deadlines = await get_upcoming_deadlines(session, user.id, days=2)
        
        # Build context
        context = {
            "current_time": datetime.utcnow().isoformat(),
            "active_tasks": [t.title for t in active_tasks[:3]],
            "upcoming_deadlines": [
                f"{d.title} (due: {d.due_date.strftime('%Y-%m-%d')})" 
                for d in deadlines[:2] if d.due_date
            ],
            "recent_activity": "Check-in",
            "energy_level": "unknown"
        }
        
        # Generate check-in message
        prompt = CHECKIN_PROMPT.format_messages(**context)
        llm = get_llm()
        response = llm.invoke(prompt)
        
        message = response.content if hasattr(response, 'content') else str(response)
        
        await application.bot.send_message(
            chat_id=user.telegram_id,
            text=message
        )
        
        logger.info(f"Sent check-in to user {user.id}")
    except Exception as e:
        logger.error(f"Error sending check-in to user {user.id}: {e}")

