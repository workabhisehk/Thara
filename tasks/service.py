"""
Task CRUD operations.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from database.models import Task, User, TaskStatus, TaskPriority, PillarType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

logger = logging.getLogger(__name__)


async def create_task(
    session: AsyncSession,
    user_id: int,
    title: str,
    description: Optional[str] = None,
    pillar: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[datetime] = None,
    estimated_duration: Optional[int] = None
) -> Task:
    """
    Create a new task with validation.
    
    Args:
        session: Database session
        user_id: User ID
        title: Task title
        description: Task description
        pillar: Pillar type (work, education, etc.)
        priority: Priority (high, medium, low)
        due_date: Due date
        estimated_duration: Estimated duration in minutes
    
    Returns:
        Created Task object
    
    Raises:
        ValueError: If validation fails
    """
    # Validate title
    from edge_cases.validation import validate_task_title
    is_valid, error_msg = validate_task_title(title)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Validate and parse pillar
    pillar_enum = PillarType.OTHER
    if pillar:
        from edge_cases.validation import validate_pillar_name
        is_valid, error_msg = validate_pillar_name(pillar)
        if not is_valid:
            logger.warning(f"Invalid pillar '{pillar}': {error_msg}, defaulting to OTHER")
        else:
            try:
                pillar_enum = PillarType(pillar.lower())
            except ValueError:
                pillar_enum = PillarType.OTHER
    
    # Validate and parse priority
    priority_enum = TaskPriority.MEDIUM
    if priority:
        from edge_cases.validation import validate_priority
        is_valid, error_msg, normalized_priority = validate_priority(priority)
        if not is_valid:
            logger.warning(f"Invalid priority '{priority}': {error_msg}, defaulting to MEDIUM")
        else:
            try:
                priority_enum = TaskPriority(normalized_priority)
            except ValueError:
                priority_enum = TaskPriority.MEDIUM
    
    # Validate description length if provided
    if description:
        from edge_cases.validation import validate_message_length
        is_valid, error_msg = validate_message_length(description, max_length=2000)
        if not is_valid:
            raise ValueError(error_msg)
    
    # Validate estimated duration if provided
    if estimated_duration is not None:
        if estimated_duration <= 0:
            raise ValueError("Estimated duration must be greater than 0 minutes.")
        if estimated_duration > 1440:  # 24 hours
            raise ValueError("Estimated duration cannot exceed 24 hours (1440 minutes).")
    
    task = Task(
        user_id=user_id,
        title=title,
        description=description,
        pillar=pillar_enum,
        priority=priority_enum,
        due_date=due_date,
        estimated_duration=estimated_duration,
        status=TaskStatus.PENDING
    )
    
    session.add(task)
    await session.flush()
    
    logger.info(f"Created task {task.id} for user {user_id}")
    return task


async def get_tasks(
    session: AsyncSession,
    user_id: int,
    status: Optional[str] = None,
    pillar: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50
) -> List[Task]:
    """
    Get tasks for user.
    
    Args:
        session: Database session
        user_id: User ID
        status: Filter by status (optional)
        pillar: Filter by pillar (optional)
        priority: Filter by priority (optional)
        limit: Maximum number of results
    
    Returns:
        List of Task objects
    """
    stmt = select(Task).where(Task.user_id == user_id)
    
    if status:
        try:
            status_enum = TaskStatus(status.lower())
            stmt = stmt.where(Task.status == status_enum)
        except ValueError:
            pass
    
    if pillar:
        try:
            pillar_enum = PillarType(pillar.lower())
            stmt = stmt.where(Task.pillar == pillar_enum)
        except ValueError:
            pass
    
    if priority:
        try:
            priority_enum = TaskPriority(priority.lower())
            stmt = stmt.where(Task.priority == priority_enum)
        except ValueError:
            pass
    
    stmt = stmt.order_by(
        Task.priority.desc(),
        Task.due_date.asc()
    ).limit(limit)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_task(session: AsyncSession, task_id: int, user_id: int) -> Optional[Task]:
    """Get a single task by ID."""
    stmt = select(Task).where(
        and_(Task.id == task_id, Task.user_id == user_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_task(
    session: AsyncSession,
    task_id: int,
    user_id: int,
    **kwargs
) -> Optional[Task]:
    """
    Update a task.
    
    Args:
        session: Database session
        task_id: Task ID
        user_id: User ID
        **kwargs: Fields to update
    
    Returns:
        Updated Task object or None
    """
    task = await get_task(session, task_id, user_id)
    if not task:
        return None
    
    # Update fields
    for key, value in kwargs.items():
        if hasattr(task, key) and value is not None:
            setattr(task, key, value)
    
    await session.flush()
    logger.info(f"Updated task {task_id}")
    return task


async def delete_task(session: AsyncSession, task_id: int, user_id: int) -> bool:
    """Delete a task."""
    task = await get_task(session, task_id, user_id)
    if not task:
        return False
    
    await session.delete(task)
    await session.flush()
    logger.info(f"Deleted task {task_id}")
    return True


async def complete_task(session: AsyncSession, task_id: int, user_id: int) -> Optional[Task]:
    """Mark task as completed."""
    task = await get_task(session, task_id, user_id)
    if not task:
        return None
    
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    
    await session.flush()
    logger.info(f"Completed task {task_id}")
    return task

