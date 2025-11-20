"""
Task dependency tracking.
"""
import logging
from typing import List, Optional
from database.models import Task, TaskStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def set_dependency(
    session: AsyncSession,
    task_id: int,
    depends_on_task_id: int,
    user_id: int
) -> bool:
    """
    Set a task dependency.
    
    Args:
        session: Database session
        task_id: Task ID
        depends_on_task_id: Task ID this task depends on
        user_id: User ID (for validation)
    
    Returns:
        True if successful
    """
    # Validate both tasks belong to user
    task = await session.get(Task, task_id)
    depends_on = await session.get(Task, depends_on_task_id)
    
    if not task or not depends_on:
        return False
    
    if task.user_id != user_id or depends_on.user_id != user_id:
        return False
    
    # Check for circular dependencies
    if await has_circular_dependency(session, task_id, depends_on_task_id):
        logger.warning(f"Circular dependency detected: {task_id} -> {depends_on_task_id}")
        return False
    
    task.depends_on_task_id = depends_on_task_id
    await session.flush()
    
    logger.info(f"Set dependency: {task_id} depends on {depends_on_task_id}")
    return True


async def has_circular_dependency(
    session: AsyncSession,
    task_id: int,
    depends_on_task_id: int,
    visited: Optional[set] = None
) -> bool:
    """Check for circular dependency."""
    if visited is None:
        visited = set()
    
    if task_id in visited:
        return True
    
    visited.add(task_id)
    
    # Get task
    task = await session.get(Task, depends_on_task_id)
    if not task or not task.depends_on_task_id:
        return False
    
    return await has_circular_dependency(
        session,
        depends_on_task_id,
        task.depends_on_task_id,
        visited
    )


async def get_blocked_tasks(
    session: AsyncSession,
    user_id: int
) -> List[Task]:
    """
    Get tasks that are blocked by incomplete dependencies.
    
    Args:
        session: Database session
        user_id: User ID
    
    Returns:
        List of blocked tasks
    """
    stmt = select(Task).where(
        Task.user_id == user_id,
        Task.depends_on_task_id.isnot(None),
        Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
    )
    
    result = await session.execute(stmt)
    all_tasks = result.scalars().all()
    
    blocked = []
    for task in all_tasks:
        if task.depends_on_task_id:
            depends_on = await session.get(Task, task.depends_on_task_id)
            if depends_on and depends_on.status != TaskStatus.COMPLETED:
                blocked.append(task)
    
    return blocked


async def can_start_task(
    session: AsyncSession,
    task_id: int
) -> bool:
    """Check if a task can be started (dependencies met)."""
    task = await session.get(Task, task_id)
    if not task or not task.depends_on_task_id:
        return True
    
    depends_on = await session.get(Task, task.depends_on_task_id)
    return depends_on and depends_on.status == TaskStatus.COMPLETED

