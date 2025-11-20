"""
Deadline monitoring and priority escalation.
"""
import logging
from typing import List
from datetime import datetime, timedelta
from database.models import Task, TaskStatus, TaskPriority
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


async def check_deadlines(session: AsyncSession, user_id: int) -> List[Task]:
    """
    Check and escalate tasks approaching deadlines.
    
    Args:
        session: Database session
        user_id: User ID
    
    Returns:
        List of escalated tasks
    """
    now = datetime.utcnow()
    
    # Tasks due within 24 hours
    urgent_cutoff = now + timedelta(hours=24)
    
    stmt = select(Task).where(
        and_(
            Task.user_id == user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            Task.due_date.isnot(None),
            Task.due_date <= urgent_cutoff,
            Task.due_date > now,
            Task.priority != TaskPriority.URGENT
        )
    )
    
    result = await session.execute(stmt)
    tasks = list(result.scalars().all())
    
    escalated = []
    for task in tasks:
        # Escalate to urgent if due within 24 hours
        if task.due_date <= urgent_cutoff:
            old_priority = task.priority
            task.priority = TaskPriority.URGENT
            escalated.append(task)
            logger.info(
                f"Escalated task {task.id} from {old_priority.value} to urgent "
                f"(due: {task.due_date})"
            )
    
    await session.flush()
    return escalated


async def mark_overdue(session: AsyncSession, user_id: int) -> List[Task]:
    """Mark overdue tasks."""
    now = datetime.utcnow()
    
    stmt = select(Task).where(
        and_(
            Task.user_id == user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            Task.due_date < now
        )
    )
    
    result = await session.execute(stmt)
    tasks = list(result.scalars().all())
    
    for task in tasks:
        task.status = TaskStatus.OVERDUE
        # Also escalate priority
        if task.priority != TaskPriority.URGENT:
            task.priority = TaskPriority.URGENT
    
    await session.flush()
    return tasks

