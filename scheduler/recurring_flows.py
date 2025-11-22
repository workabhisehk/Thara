"""
Scheduled job for checking enabled recurring flows and sending reminders.
According to COMPREHENSIVE_PLAN.md Section 9: Adaptive Learning & Self-Improvement
"""
import logging
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from memory.flow_enabler import (
    check_enabled_flows_for_reminders,
    send_recurring_task_reminder
)
from telegram_bot.bot import create_application

logger = logging.getLogger(__name__)


async def check_recurring_flows():
    """Check enabled flows and send reminders for all active users."""
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
                # Check for reminders needed
                reminders_needed = await check_enabled_flows_for_reminders(
                    session,
                    user.id
                )
                
                # Send reminders
                for reminder_info in reminders_needed:
                    await send_recurring_task_reminder(
                        session,
                        user.id,
                        reminder_info,
                        application
                    )
                
                await session.commit()
                
                if reminders_needed:
                    logger.info(f"Sent {len(reminders_needed)} recurring flow reminders to user {user.id}")
                    
            except Exception as e:
                logger.error(f"Error checking recurring flows for user {user.id}: {e}")

