"""
Pattern learning and habit recognition from user behavior.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from database.models import Task, Habit, User, Analytics
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from collections import defaultdict

logger = logging.getLogger(__name__)


async def analyze_task_completion_patterns(
    session: AsyncSession,
    user_id: int,
    days: int = 30
) -> Dict[str, Any]:
    """
    Analyze task completion patterns for a user.
    
    Args:
        session: Database session
        user_id: User ID
        days: Number of days to analyze
    
    Returns:
        Dictionary with pattern analysis
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get completed tasks
    stmt = select(Task).where(
        Task.user_id == user_id,
        Task.status == "completed",
        Task.completed_at >= cutoff_date
    )
    
    result = await session.execute(stmt)
    completed_tasks = result.scalars().all()
    
    patterns = {
        "average_completion_time": 0,
        "pillar_distribution": defaultdict(int),
        "priority_distribution": defaultdict(int),
        "completion_rate_by_pillar": {},
        "preferred_work_times": []
    }
    
    if not completed_tasks:
        return patterns
    
    # Calculate average completion time
    total_duration = 0
    count = 0
    for task in completed_tasks:
        if task.actual_duration:
            total_duration += task.actual_duration
            count += 1
        elif task.estimated_duration:
            total_duration += task.estimated_duration
            count += 1
    
    if count > 0:
        patterns["average_completion_time"] = total_duration / count
    
    # Pillar distribution
    for task in completed_tasks:
        patterns["pillar_distribution"][task.pillar.value] += 1
    
    # Priority distribution
    for task in completed_tasks:
        patterns["priority_distribution"][task.priority.value] += 1
    
    # Completion rate by pillar
    for pillar in patterns["pillar_distribution"]:
        total_stmt = select(func.count(Task.id)).where(
            Task.user_id == user_id,
            Task.pillar == pillar,
            Task.created_at >= cutoff_date
        )
        total_result = await session.execute(total_stmt)
        total = total_result.scalar() or 1
        
        completed = patterns["pillar_distribution"][pillar]
        patterns["completion_rate_by_pillar"][pillar] = completed / total if total > 0 else 0
    
    return patterns


async def detect_habits(
    session: AsyncSession,
    user_id: int
) -> List[Habit]:
    """
    Detect and create habit records from user behavior.
    
    Args:
        session: Database session
        user_id: User ID
    
    Returns:
        List of Habit objects
    """
    habits = []
    
    # Analyze patterns
    patterns = await analyze_task_completion_patterns(session, user_id)
    
    # Create habit for average completion time
    if patterns["average_completion_time"] > 0:
        existing = await session.execute(
            select(Habit).where(
                Habit.user_id == user_id,
                Habit.pattern_type == "task_completion_time"
            )
        )
        habit = existing.scalar_one_or_none()
        
        if habit:
            habit.pattern_data = {"average_minutes": patterns["average_completion_time"]}
            habit.confidence_score = min(1.0, len(patterns["pillar_distribution"]) / 10.0)
            habit.last_observed_at = datetime.utcnow()
        else:
            habit = Habit(
                user_id=user_id,
                pattern_type="task_completion_time",
                pattern_data={"average_minutes": patterns["average_completion_time"]},
                confidence_score=min(1.0, len(patterns["pillar_distribution"]) / 10.0),
                last_observed_at=datetime.utcnow()
            )
            session.add(habit)
        
        habits.append(habit)
    
    # Create habit for pillar preferences
    if patterns["pillar_distribution"]:
        most_common_pillar = max(
            patterns["pillar_distribution"].items(),
            key=lambda x: x[1]
        )[0]
        
        existing = await session.execute(
            select(Habit).where(
                Habit.user_id == user_id,
                Habit.pattern_type == "preferred_pillar"
            )
        )
        habit = existing.scalar_one_or_none()
        
        if habit:
            habit.pattern_data = {
                "preferred_pillar": most_common_pillar,
                "distribution": dict(patterns["pillar_distribution"])
            }
            habit.confidence_score = patterns["pillar_distribution"][most_common_pillar] / sum(patterns["pillar_distribution"].values())
            habit.last_observed_at = datetime.utcnow()
        else:
            habit = Habit(
                user_id=user_id,
                pattern_type="preferred_pillar",
                pattern_data={
                    "preferred_pillar": most_common_pillar,
                    "distribution": dict(patterns["pillar_distribution"])
                },
                confidence_score=patterns["pillar_distribution"][most_common_pillar] / sum(patterns["pillar_distribution"].values()),
                last_observed_at=datetime.utcnow()
            )
            session.add(habit)
        
        habits.append(habit)
    
    await session.flush()
    return habits


async def get_user_habits(
    session: AsyncSession,
    user_id: int
) -> List[Habit]:
    """
    Get all habits for a user.
    
    Args:
        session: Database session
        user_id: User ID
    
    Returns:
        List of Habit objects
    """
    stmt = select(Habit).where(
        Habit.user_id == user_id
    ).order_by(
        Habit.confidence_score.desc()
    )
    
    result = await session.execute(stmt)
    return list(result.scalars().all())

