"""
Duplicate task detection using similarity matching.
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from database.models import Task, TaskStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def calculate_string_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity between two strings (0.0 to 1.0).
    
    Uses SequenceMatcher for fuzzy matching.
    """
    return SequenceMatcher(None, str1.lower().strip(), str2.lower().strip()).ratio()


def normalize_title(title: str) -> str:
    """
    Normalize task title for comparison.
    
    Removes common words and normalizes spacing.
    """
    # Remove common prefixes
    prefixes = ["add", "create", "new", "task", "reminder", "todo"]
    title_lower = title.lower().strip()
    
    for prefix in prefixes:
        if title_lower.startswith(prefix):
            title_lower = title_lower[len(prefix):].strip(": ,")
    
    # Normalize whitespace
    import re
    title_lower = re.sub(r'\s+', ' ', title_lower).strip()
    
    return title_lower


async def find_duplicate_tasks(
    session: AsyncSession,
    user_id: int,
    title: str,
    due_date: Optional[datetime] = None,
    similarity_threshold: float = 0.85,
    days_window: int = 7
) -> List[Tuple[Task, float, str]]:
    """
    Find potential duplicate tasks.
    
    Args:
        session: Database session
        user_id: User ID
        title: New task title
        due_date: New task due date (optional)
        similarity_threshold: Minimum similarity score (0.0-1.0)
        days_window: Days around due_date to check for duplicates
    
    Returns:
        List of tuples: (Task, similarity_score, reason)
    """
    duplicates = []
    
    # Get all active/pending tasks for the user
    stmt = select(Task).where(
        and_(
            Task.user_id == user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        )
    )
    
    result = await session.execute(stmt)
    existing_tasks = result.scalars().all()
    
    normalized_new_title = normalize_title(title)
    
    for task in existing_tasks:
        similarity_score = 0.0
        reasons = []
        
        # Check title similarity
        normalized_existing_title = normalize_title(task.title)
        title_similarity = calculate_string_similarity(
            normalized_new_title,
            normalized_existing_title
        )
        
        if title_similarity >= similarity_threshold:
            similarity_score = title_similarity
            reasons.append(f"Similar title: '{task.title}'")
        
        # Check exact title match (case-insensitive)
        if normalized_new_title == normalized_existing_title:
            similarity_score = max(similarity_score, 1.0)
            reasons.append(f"Exact title match: '{task.title}'")
        
        # Check due date proximity if both have due dates
        if due_date and task.due_date:
            date_diff = abs((due_date - task.due_date).total_seconds())
            days_diff = date_diff / (24 * 3600)
            
            if days_diff <= days_window:
                # Boost similarity if dates are close
                date_similarity = 1.0 - (days_diff / days_window)
                similarity_score = max(similarity_score, date_similarity * 0.3)
                reasons.append(f"Similar due date: {task.due_date.strftime('%Y-%m-%d')}")
        
        # If similarity is high enough, add to duplicates
        if similarity_score >= similarity_threshold:
            reason = " | ".join(reasons) if reasons else "Potential duplicate"
            duplicates.append((task, similarity_score, reason))
    
    # Sort by similarity (highest first)
    duplicates.sort(key=lambda x: x[1], reverse=True)
    
    return duplicates


async def check_for_duplicates(
    session: AsyncSession,
    user_id: int,
    title: str,
    due_date: Optional[datetime] = None,
    similarity_threshold: float = 0.85
) -> Optional[Dict[str, Any]]:
    """
    Check if a task is a duplicate and return information.
    
    Args:
        session: Database session
        user_id: User ID
        title: New task title
        due_date: New task due date (optional)
        similarity_threshold: Minimum similarity score
    
    Returns:
        Dictionary with duplicate info if found, None otherwise:
        {
            "is_duplicate": bool,
            "similar_tasks": List[Dict],
            "highest_similarity": float,
            "message": str
        }
    """
    duplicates = await find_duplicate_tasks(
        session,
        user_id,
        title,
        due_date,
        similarity_threshold
    )
    
    if not duplicates:
        return None
    
    # Format similar tasks
    similar_tasks = []
    for task, score, reason in duplicates[:3]:  # Limit to top 3
        similar_tasks.append({
            "id": task.id,
            "title": task.title,
            "due_date": task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else None,
            "status": task.status.value,
            "similarity": score,
            "reason": reason
        })
    
    highest_similarity = duplicates[0][1]
    
    # Generate message
    if highest_similarity >= 0.95:
        message = f"⚠️ **Exact or near-exact duplicate detected!**\n\n"
    elif highest_similarity >= 0.85:
        message = f"⚠️ **Similar task found!**\n\n"
    else:
        message = f"ℹ️ **Potentially similar task found:**\n\n"
    
    message += f"I found {len(duplicates)} similar task(s):\n\n"
    
    for i, task_info in enumerate(similar_tasks, 1):
        message += f"{i}. **{task_info['title']}**\n"
        if task_info['due_date']:
            message += f"   Due: {task_info['due_date']}\n"
        message += f"   Status: {task_info['status']}\n"
        message += f"   Similarity: {task_info['similarity']:.0%}\n\n"
    
    message += "Do you want to create this task anyway, or would you like to update the existing one?"
    
    return {
        "is_duplicate": highest_similarity >= 0.85,
        "similar_tasks": similar_tasks,
        "highest_similarity": highest_similarity,
        "message": message
    }

