"""
Task completion metrics and tracking.
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from database.models import Task, User, Analytics
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

logger = logging.getLogger(__name__)


async def get_weekly_stats(session: AsyncSession, user_id: int) -> Dict[str, Any]:
    """
    Get weekly statistics for user.
    
    Args:
        session: Database session
        user_id: User ID
    
    Returns:
        Dictionary with weekly stats
    """
    week_start = datetime.utcnow() - timedelta(days=7)
    
    # Completed tasks
    completed_stmt = select(func.count(Task.id)).where(
        and_(
            Task.user_id == user_id,
            Task.status == "completed",
            Task.completed_at >= week_start
        )
    )
    completed_result = await session.execute(completed_stmt)
    completed = completed_result.scalar() or 0
    
    # Created tasks
    created_stmt = select(func.count(Task.id)).where(
        and_(
            Task.user_id == user_id,
            Task.created_at >= week_start
        )
    )
    created_result = await session.execute(created_stmt)
    created = created_result.scalar() or 0
    
    # Overdue tasks
    overdue_stmt = select(func.count(Task.id)).where(
        and_(
            Task.user_id == user_id,
            Task.status == "overdue"
        )
    )
    overdue_result = await session.execute(overdue_stmt)
    overdue = overdue_result.scalar() or 0
    
    # Completion rate
    completion_rate = (completed / created * 100) if created > 0 else 0
    
    return {
        "completed": completed,
        "created": created,
        "overdue": overdue,
        "completion_rate": completion_rate
    }


async def get_pillar_stats(session: AsyncSession, user_id: int, days: int = 30) -> Dict[str, Dict[str, Any]]:
    """
    Get statistics by pillar.
    
    Args:
        session: Database session
        user_id: User ID
        days: Number of days to analyze
    
    Returns:
        Dictionary with stats per pillar
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    from database.models import PillarType
    
    stats = {}
    for pillar in PillarType:
        # Completed
        completed_stmt = select(func.count(Task.id)).where(
            and_(
                Task.user_id == user_id,
                Task.pillar == pillar,
                Task.status == "completed",
                Task.completed_at >= cutoff
            )
        )
        completed_result = await session.execute(completed_stmt)
        completed = completed_result.scalar() or 0
        
        # Total
        total_stmt = select(func.count(Task.id)).where(
            and_(
                Task.user_id == user_id,
                Task.pillar == pillar,
                Task.created_at >= cutoff
            )
        )
        total_result = await session.execute(total_stmt)
        total = total_result.scalar() or 0
        
        stats[pillar.value] = {
            "completed": completed,
            "total": total,
            "completion_rate": (completed / total * 100) if total > 0 else 0
        }
    
    return stats

