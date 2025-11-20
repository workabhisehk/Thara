"""
Priority queue management for tasks.
"""
import logging
from typing import List
from datetime import datetime, timedelta
from database.models import Task, TaskStatus, TaskPriority
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

logger = logging.getLogger(__name__)


async def get_priority_queue(
    session: AsyncSession,
    user_id: int,
    limit: int = 10
) -> List[Task]:
    """
    Get tasks ordered by priority and urgency.
    
    Args:
        session: Database session
        user_id: User ID
        limit: Maximum number of tasks
    
    Returns:
        List of tasks ordered by priority
    """
    stmt = select(Task).where(
        and_(
            Task.user_id == user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        )
    ).order_by(
        # Urgent tasks first
        Task.priority.desc(),
        # Then by due date (earliest first)
        Task.due_date.asc().nulls_last(),
        # Then by creation date
        Task.created_at.asc()
    ).limit(limit)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_overdue_tasks(
    session: AsyncSession,
    user_id: int
) -> List[Task]:
    """Get overdue tasks."""
    now = datetime.utcnow()
    
    stmt = select(Task).where(
        and_(
            Task.user_id == user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            Task.due_date < now
        )
    ).order_by(
        Task.due_date.asc()
    )
    
    result = await session.execute(stmt)
    tasks = list(result.scalars().all())
    
    # Update status to overdue
    for task in tasks:
        if task.status != TaskStatus.OVERDUE:
            task.status = TaskStatus.OVERDUE
    
    await session.flush()
    return tasks


async def get_upcoming_deadlines(
    session: AsyncSession,
    user_id: int,
    days: int = 3
) -> List[Task]:
    """Get tasks with upcoming deadlines."""
    now = datetime.utcnow()
    cutoff = now + timedelta(days=days)
    
    stmt = select(Task).where(
        and_(
            Task.user_id == user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            Task.due_date >= now,
            Task.due_date <= cutoff
        )
    ).order_by(
        Task.due_date.asc()
    )
    
    result = await session.execute(stmt)
    return list(result.scalars().all())

