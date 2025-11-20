"""
Scheduled job for time-based task reminders.
"""
import logging
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from tasks.time_based_reminders import send_time_based_reminders

logger = logging.getLogger(__name__)


async def check_time_based_reminders():
    """Check and send time-based reminders for all active users."""
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
                await send_time_based_reminders(session, user.id)
            except Exception as e:
                logger.error(f"Error checking time reminders for user {user.id}: {e}")

