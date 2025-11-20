"""
Clarification queue management.
"""
import logging
from typing import List, Optional
from datetime import datetime
from database.models import Clarification, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


async def add_clarification(
    session: AsyncSession,
    user_id: int,
    question: str,
    context: Optional[dict] = None,
    related_task_id: Optional[int] = None,
    priority: int = 1
) -> Clarification:
    """
    Add a clarification to the queue.
    
    Args:
        session: Database session
        user_id: User ID
        question: Question to ask
        context: Context about what needs clarification
        related_task_id: Related task ID (optional)
        priority: Priority (higher = more urgent)
    
    Returns:
        Created Clarification object
    """
    clarification = Clarification(
        user_id=user_id,
        question=question,
        context=context or {},
        related_task_id=related_task_id,
        priority=priority
    )
    
    session.add(clarification)
    await session.flush()
    
    logger.info(f"Added clarification {clarification.id} for user {user_id}")
    return clarification


async def get_pending_clarifications(
    session: AsyncSession,
    user_id: int,
    limit: int = 10
) -> List[Clarification]:
    """
    Get pending clarifications for user.
    
    Args:
        session: Database session
        user_id: User ID
        limit: Maximum number of results
    
    Returns:
        List of pending Clarification objects
    """
    stmt = select(Clarification).where(
        and_(
            Clarification.user_id == user_id,
            Clarification.is_resolved == False
        )
    ).order_by(
        Clarification.priority.desc(),
        Clarification.created_at.asc()
    ).limit(limit)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def resolve_clarification(
    session: AsyncSession,
    clarification_id: int,
    answer: str
) -> bool:
    """
    Resolve a clarification.
    
    Args:
        session: Database session
        clarification_id: Clarification ID
        answer: Answer provided
    
    Returns:
        True if successful
    """
    clarification = await session.get(Clarification, clarification_id)
    if not clarification:
        return False
    
    clarification.is_resolved = True
    clarification.answer = answer
    clarification.resolved_at = datetime.utcnow()
    
    await session.flush()
    logger.info(f"Resolved clarification {clarification_id}")
    return True

