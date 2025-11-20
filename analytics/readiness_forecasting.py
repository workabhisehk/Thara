"""
Readiness forecasting for deadlines.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from database.models import Task, TaskStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from tasks.priority_queue import get_upcoming_deadlines

logger = logging.getLogger(__name__)


async def calculate_readiness_scores(
    session: AsyncSession,
    user_id: int,
    days: int = 7
) -> List[Dict[str, Any]]:
    """
    Calculate readiness scores for upcoming deadlines.
    
    Args:
        session: Database session
        user_id: User ID
        days: Number of days to look ahead
    
    Returns:
        List of readiness scores for tasks
    """
    tasks = await get_upcoming_deadlines(session, user_id, days=days)
    
    readiness_scores = []
    now = datetime.utcnow()
    
    for task in tasks:
        if not task.due_date:
            continue
        
        # Calculate time until deadline
        time_until_deadline = (task.due_date - now).total_seconds() / 3600  # hours
        
        # Estimate time needed (use estimated_duration or default)
        time_needed = (task.estimated_duration or 60) / 60  # hours
        
        # Calculate readiness (0-100)
        if time_until_deadline <= 0:
            readiness = 0  # Overdue
        elif time_until_deadline >= time_needed * 2:
            readiness = 100  # Plenty of time
        else:
            # Linear interpolation
            readiness = min(100, max(0, (time_until_deadline / (time_needed * 2)) * 100))
        
        # Adjust based on task status
        if task.status == TaskStatus.IN_PROGRESS:
            readiness += 20  # Bonus for in progress
        elif task.status == TaskStatus.PENDING:
            readiness -= 10  # Penalty for not started
        
        readiness = min(100, max(0, readiness))
        
        readiness_scores.append({
            "task_id": task.id,
            "task_title": task.title,
            "due_date": task.due_date.isoformat(),
            "readiness_score": readiness,
            "time_until_deadline_hours": time_until_deadline,
            "estimated_hours_needed": time_needed
        })
    
    # Sort by readiness (lowest first - most urgent)
    readiness_scores.sort(key=lambda x: x["readiness_score"])
    
    return readiness_scores

