"""
Process user feedback for learning and adaptation.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from database.models import LearningFeedback, User, Habit
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from memory.pattern_learning import detect_habits

logger = logging.getLogger(__name__)


async def store_feedback(
    session: AsyncSession,
    user_id: int,
    feedback_type: str,
    context: Dict[str, Any],
    rating: Optional[int] = None,
    comment: Optional[str] = None
) -> LearningFeedback:
    """
    Store user feedback.
    
    Args:
        session: Database session
        user_id: User ID
        feedback_type: Type of feedback (e.g., "suggestion_rating", "plan_feedback")
        context: Context about what the feedback is about
        rating: Rating 1-5 (optional)
        comment: Text comment (optional)
    
    Returns:
        Created LearningFeedback object
    """
    feedback = LearningFeedback(
        user_id=user_id,
        feedback_type=feedback_type,
        context=context,
        rating=rating,
        comment=comment
    )
    
    session.add(feedback)
    await session.flush()
    
    logger.info(f"Stored feedback {feedback.id} for user {user_id}")
    
    # If feedback indicates pattern change, update habits
    if rating and rating <= 2:  # Negative feedback
        await detect_habits(session, user_id)
    
    return feedback


async def get_feedback_summary(
    session: AsyncSession,
    user_id: int,
    feedback_type: Optional[str] = None,
    days: int = 30
) -> Dict[str, Any]:
    """
    Get summary of user feedback.
    
    Args:
        session: Database session
        user_id: User ID
        feedback_type: Filter by type (optional)
        days: Number of days to look back
    
    Returns:
        Dictionary with feedback summary
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    stmt = select(LearningFeedback).where(
        LearningFeedback.user_id == user_id,
        LearningFeedback.created_at >= cutoff_date
    )
    
    if feedback_type:
        stmt = stmt.where(LearningFeedback.feedback_type == feedback_type)
    
    result = await session.execute(stmt)
    feedbacks = result.scalars().all()
    
    if not feedbacks:
        return {
            "total": 0,
            "average_rating": None,
            "positive_count": 0,
            "negative_count": 0
        }
    
    ratings = [f.rating for f in feedbacks if f.rating is not None]
    
    return {
        "total": len(feedbacks),
        "average_rating": sum(ratings) / len(ratings) if ratings else None,
        "positive_count": len([f for f in feedbacks if f.rating and f.rating >= 4]),
        "negative_count": len([f for f in feedbacks if f.rating and f.rating <= 2]),
        "by_type": {}
    }

