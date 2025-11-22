"""
Adaptive learning: Learn from mistakes, detect patterns, create automatic flows.
According to COMPREHENSIVE_PLAN.md Section 9: Adaptive Learning & Self-Improvement
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from database.models import Task, LearningFeedback, Conversation, User, Habit
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


async def learn_from_correction(
    session: AsyncSession,
    user_id: int,
    correction_type: str,
    original_value: Any,
    corrected_value: Any,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Learn from user corrections.
    
    When a user corrects:
    - Pillar assignment → Learn preferred categorization
    - Priority assignment → Learn priority preferences
    - Due date → Learn deadline patterns
    - Task title/description → Learn language patterns
    - Scheduling time → Learn preferred work times
    
    Args:
        session: Database session
        user_id: User ID
        correction_type: Type of correction ("pillar", "priority", "due_date", "title", "scheduling")
        original_value: Original AI-suggested value
        corrected_value: User's corrected value
        context: Additional context (task description, etc.)
    
    Returns:
        Dictionary with learning insights
    """
    try:
        # Store correction as feedback
        from memory.feedback_processor import store_feedback
        
        await store_feedback(
            session,
            user_id,
            feedback_type=f"correction_{correction_type}",
            context={
                "original": str(original_value),
                "corrected": str(corrected_value),
                **context
            },
            rating=3  # Neutral rating, but indicates correction
        )
        
        # Analyze correction pattern
        insights = {
            "correction_type": correction_type,
            "pattern_detected": False,
            "recommendation": None
        }
        
        # Get recent corrections of same type
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        feedbacks_stmt = select(LearningFeedback).where(
            and_(
                LearningFeedback.user_id == user_id,
                LearningFeedback.feedback_type == f"correction_{correction_type}",
                LearningFeedback.created_at >= cutoff_date
            )
        )
        feedbacks_result = await session.execute(feedbacks_stmt)
        recent_corrections = feedbacks_result.scalars().all()
        
        if len(recent_corrections) >= 3:
            # Pattern detected - user consistently corrects this type
            corrections_by_context = defaultdict(list)
            for fb in recent_corrections:
                # Group by context similarity (e.g., task descriptions)
                context_key = fb.context.get("task_description", "")[:50]
                corrections_by_context[context_key].append(fb.context.get("corrected"))
            
            # Find most common correction pattern
            for context_key, corrections in corrections_by_context.items():
                if len(corrections) >= 2:
                    most_common = Counter(corrections).most_common(1)[0]
                    if most_common[1] >= 2:
                        insights["pattern_detected"] = True
                        insights["recommendation"] = (
                            f"When categorizing similar tasks to '{context_key[:30]}...', "
                            f"consider using '{most_common[0]}' instead."
                        )
                        break
        
        await session.commit()
        logger.info(f"Learned from correction for user {user_id}: {correction_type}")
        
        return insights
        
    except Exception as e:
        logger.error(f"Error learning from correction: {e}")
        return {"error": str(e)}


async def detect_recurring_patterns(
    session: AsyncSession,
    user_id: int,
    pattern_type: str = "task_creation"
) -> List[Dict[str, Any]]:
    """
    Detect recurring patterns in user behavior.
    
    Patterns detected:
    1. Recurring task patterns (same task created regularly)
    2. Time-based patterns (tasks created at specific times)
    3. Sequential patterns (tasks often created together)
    4. Categorization patterns (similar tasks get same pillar/priority)
    
    Args:
        session: Database session
        user_id: User ID
        pattern_type: Type of pattern to detect ("task_creation", "completion", "scheduling")
    
    Returns:
        List of detected patterns with confidence scores
    """
    patterns = []
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=60)
        
        if pattern_type == "task_creation":
            # Detect recurring task titles/patterns
            stmt = select(Task).where(
                and_(
                    Task.user_id == user_id,
                    Task.created_at >= cutoff_date
                )
            ).order_by(Task.created_at.desc())
            
            result = await session.execute(stmt)
            tasks = result.scalars().all()
            
            # Group by similar titles
            title_groups = defaultdict(list)
            for task in tasks:
                # Normalize title for comparison
                normalized = task.title.lower().strip()
                # Simple grouping by first few words
                key_words = " ".join(normalized.split()[:3])
                title_groups[key_words].append(task)
            
            # Find recurring patterns
            for key_words, task_group in title_groups.items():
                if len(task_group) >= 3:  # At least 3 occurrences
                    # Check if tasks are created regularly
                    creation_dates = sorted([t.created_at for t in task_group])
                    
                    # Calculate time intervals
                    intervals = []
                    for i in range(1, len(creation_dates)):
                        delta = (creation_dates[i] - creation_dates[i-1]).total_seconds() / 86400  # days
                        intervals.append(delta)
                    
                    if intervals:
                        avg_interval = sum(intervals) / len(intervals)
                        # Check if interval is regular (within 20% variance)
                        variance = sum([abs(x - avg_interval) for x in intervals]) / len(intervals)
                        is_regular = variance / avg_interval < 0.2 if avg_interval > 0 else False
                        
                        if is_regular:
                            patterns.append({
                                "type": "recurring_task",
                                "pattern": key_words,
                                "frequency_days": avg_interval,
                                "occurrences": len(task_group),
                                "confidence": min(1.0, len(task_group) / 10.0),
                                "sample_tasks": [t.title for t in task_group[:3]],
                                "next_expected": creation_dates[-1] + timedelta(days=avg_interval)
                            })
        
        elif pattern_type == "completion":
            # Detect completion time patterns
            stmt = select(Task).where(
                and_(
                    Task.user_id == user_id,
                    Task.status == "completed",
                    Task.completed_at >= cutoff_date,
                    Task.completed_at.isnot(None)
                )
            )
            
            result = await session.execute(stmt)
            completed_tasks = result.scalars().all()
            
            if completed_tasks:
                # Analyze completion times of day
                completion_hours = [t.completed_at.hour for t in completed_tasks if t.completed_at]
                if completion_hours:
                    hour_counter = Counter(completion_hours)
                    most_common_hour = hour_counter.most_common(1)[0]
                    
                    if most_common_hour[1] >= len(completion_hours) * 0.3:  # 30% or more
                        patterns.append({
                            "type": "completion_time",
                            "preferred_hour": most_common_hour[0],
                            "confidence": most_common_hour[1] / len(completion_hours),
                            "sample_size": len(completion_hours)
                        })
        
        elif pattern_type == "scheduling":
            # Detect scheduling preferences
            stmt = select(Task).where(
                and_(
                    Task.user_id == user_id,
                    Task.scheduled_start.isnot(None),
                    Task.scheduled_start >= cutoff_date
                )
            )
            
            result = await session.execute(stmt)
            scheduled_tasks = result.scalars().all()
            
            if scheduled_tasks:
                # Analyze preferred scheduling times
                scheduling_hours = [t.scheduled_start.hour for t in scheduled_tasks if t.scheduled_start]
                if scheduling_hours:
                    hour_counter = Counter(scheduling_hours)
                    most_common_hour = hour_counter.most_common(1)[0]
                    
                    if most_common_hour[1] >= len(scheduling_hours) * 0.3:
                        patterns.append({
                            "type": "scheduling_preference",
                            "preferred_hour": most_common_hour[0],
                            "confidence": most_common_hour[1] / len(scheduling_hours),
                            "sample_size": len(scheduling_hours)
                        })
        
        logger.info(f"Detected {len(patterns)} patterns for user {user_id}: {pattern_type}")
        
    except Exception as e:
        logger.error(f"Error detecting recurring patterns: {e}")
    
    return patterns


async def suggest_automatic_flow(
    session: AsyncSession,
    user_id: int,
    pattern: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Suggest automatic flow creation based on detected pattern.
    
    When a recurring pattern is detected, suggest creating an automatic flow:
    - Recurring task → Suggest habit or recurring task
    - Time-based pattern → Suggest scheduled reminder
    - Sequential pattern → Suggest task template
    
    Args:
        session: Database session
        user_id: User ID
        pattern: Detected pattern dictionary
    
    Returns:
        Suggested automatic flow or None
    """
    try:
        if pattern["type"] == "recurring_task" and pattern["confidence"] > 0.7:
            # Suggest recurring task/habit
            return {
                "flow_type": "recurring_task",
                "title": f"Recurring: {pattern['sample_tasks'][0]}",
                "description": (
                    f"I noticed you create this task every {pattern['frequency_days']:.0f} days. "
                    f"Would you like me to automatically remind you to create it?"
                ),
                "pattern": pattern,
                "suggested_frequency": pattern["frequency_days"],
                "next_reminder": pattern["next_expected"]
            }
        
        elif pattern["type"] == "completion_time" and pattern["confidence"] > 0.6:
            # Suggest optimizing task timing based on completion patterns
            return {
                "flow_type": "completion_optimization",
                "description": (
                    f"You tend to complete tasks around {pattern['preferred_hour']}:00. "
                    f"Would you like me to suggest scheduling tasks around this time?"
                ),
                "pattern": pattern
            }
        
        elif pattern["type"] == "scheduling_preference" and pattern["confidence"] > 0.6:
            # Suggest using preferred scheduling time as default
            return {
                "flow_type": "default_scheduling_time",
                "description": (
                    f"You prefer scheduling tasks around {pattern['preferred_hour']}:00. "
                    f"Should I use this as your default scheduling time?"
                ),
                "pattern": pattern
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error suggesting automatic flow: {e}")
        return None


async def adapt_behavior_from_patterns(
    session: AsyncSession,
    user_id: int
) -> Dict[str, Any]:
    """
    Adapt agent behavior based on learned patterns.
    
    Adapts:
    - Check-in timing → Adjust to user's active hours
    - Suggestion timing → Suggest at optimal times
    - Priority suggestions → Learn from corrections
    - Default values → Use learned preferences
    
    Args:
        session: Database session
        user_id: User ID
    
    Returns:
        Dictionary with behavior adaptations
    """
    adaptations = {
        "check_in_timing": None,
        "suggestion_timing": None,
        "default_priority": None,
        "default_pillar": None,
        "preferred_work_hours": None
    }
    
    try:
        # Get user's habits
        from memory.pattern_learning import get_user_habits
        habits = await get_user_habits(session, user_id)
        
        # Get patterns
        completion_patterns = await detect_recurring_patterns(session, user_id, "completion")
        scheduling_patterns = await detect_recurring_patterns(session, user_id, "scheduling")
        
        # Adapt check-in timing based on completion patterns
        if completion_patterns:
            completion_pattern = completion_patterns[0]
            if completion_pattern["type"] == "completion_time":
                preferred_hour = completion_pattern["preferred_hour"]
                # Suggest check-ins 1 hour before preferred completion time
                adaptations["check_in_timing"] = {
                    "suggested_hour": (preferred_hour - 1) % 24,
                    "confidence": completion_pattern["confidence"]
                }
        
        # Adapt suggestion timing based on scheduling patterns
        if scheduling_patterns:
            scheduling_pattern = scheduling_patterns[0]
            if scheduling_pattern["type"] == "scheduling_preference":
                adaptations["suggestion_timing"] = {
                    "suggested_hour": scheduling_pattern["preferred_hour"],
                    "confidence": scheduling_pattern["confidence"]
                }
        
        # Adapt default values from habit preferences
        for habit in habits:
            if habit.pattern_type == "preferred_pillar":
                pillar_data = habit.pattern_data or {}
                if "preferred_pillar" in pillar_data:
                    adaptations["default_pillar"] = {
                        "pillar": pillar_data["preferred_pillar"],
                        "confidence": habit.confidence_score
                    }
        
        # Get user preferences
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            adaptations["preferred_work_hours"] = {
                "start": user.work_start_hour or 8,
                "end": user.work_end_hour or 20
            }
        
        logger.info(f"Adapted behavior for user {user_id}: {adaptations}")
        
    except Exception as e:
        logger.error(f"Error adapting behavior from patterns: {e}")
    
    return adaptations


async def track_correction_and_learn(
    session: AsyncSession,
    user_id: int,
    action: str,
    original_value: Any,
    corrected_value: Any,
    context: Dict[str, Any]
) -> None:
    """
    Convenience function to track corrections and trigger learning.
    
    Call this whenever a user corrects an AI suggestion:
    - Edits task pillar → track_correction_and_learn(..., "pillar", ...)
    - Changes priority → track_correction_and_learn(..., "priority", ...)
    - Reschedules task → track_correction_and_learn(..., "scheduling", ...)
    
    Args:
        session: Database session
        user_id: User ID
        action: Action that was corrected
        original_value: Original AI value
        corrected_value: User's corrected value
        context: Additional context
    """
    try:
        # Learn from correction
        insights = await learn_from_correction(
            session,
            user_id,
            action,
            original_value,
            corrected_value,
            context
        )
        
        # If pattern detected, check if we should suggest automatic flow
        if insights.get("pattern_detected"):
            patterns = await detect_recurring_patterns(session, user_id)
            
            for pattern in patterns:
                if pattern["confidence"] > 0.7:
                    flow_suggestion = await suggest_automatic_flow(session, user_id, pattern)
                    if flow_suggestion:
                        logger.info(f"Suggested automatic flow for user {user_id}: {flow_suggestion['flow_type']}")
                        # Store suggestion for user notification (will be sent via insights handler)
                        # The pattern is already stored in LearningFeedback, so it can be retrieved later
        
    except Exception as e:
        logger.error(f"Error tracking correction and learning: {e}")

