"""
Inactivity detection and passive mode.
"""
import logging
from datetime import datetime, timedelta
from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

logger = logging.getLogger(__name__)


async def check_inactivity(session: AsyncSession, user_id: int, hours: int = 24) -> bool:
    """
    Check if user has been inactive.
    
    Args:
        session: Database session
        user_id: User ID
        hours: Hours of inactivity threshold
    
    Returns:
        True if inactive
    """
    user = await session.get(User, user_id)
    if not user:
        return False
    
    if not user.last_active_at:
        return True
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    return user.last_active_at < cutoff


async def enter_passive_mode(session: AsyncSession, user_id: int):
    """Enter passive mode for user (reduce check-in frequency)."""
    stmt = update(User).where(
        User.id == user_id
    ).values(
        is_active=False  # Use this flag to reduce frequency
    )
    await session.execute(stmt)
    await session.commit()
    logger.info(f"User {user_id} entered passive mode")


async def resume_active_mode(session: AsyncSession, user_id: int):
    """Resume active mode for user."""
    stmt = update(User).where(
        User.id == user_id
    ).values(
        is_active=True,
        last_active_at=datetime.utcnow()
    )
    await session.execute(stmt)
    await session.commit()
    logger.info(f"User {user_id} resumed active mode")

