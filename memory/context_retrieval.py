"""
Context retrieval using semantic search for personalized suggestions.
"""
import logging
from typing import List, Dict, Any, Optional
from memory.llamaindex_setup import get_index
from memory.conversation_store import retrieve_relevant_conversations, get_recent_conversations
from database.models import Task, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def get_context_for_ai(
    session: AsyncSession,
    user_id: int,
    query: str,
    include_recent: bool = True,
    include_tasks: bool = True,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get comprehensive context for AI interactions.
    
    Args:
        session: Database session
        user_id: User ID
        query: Current query/context
        include_recent: Include recent conversations
        include_tasks: Include relevant tasks
        limit: Maximum results per source
    
    Returns:
        Dictionary with context from various sources
    """
    context = {
        "relevant_conversations": [],
        "recent_conversations": [],
        "relevant_tasks": [],
        "user_preferences": {}
    }
    
    # Get relevant conversations via semantic search
    try:
        relevant = await retrieve_relevant_conversations(user_id, query, limit=limit)
        context["relevant_conversations"] = relevant
    except Exception as e:
        logger.error(f"Error retrieving relevant conversations: {e}")
    
    # Get recent conversations
    if include_recent:
        try:
            recent = await get_recent_conversations(session, user_id, limit=limit)
            context["recent_conversations"] = [
                {
                    "text": conv.text,
                    "is_from_user": conv.is_from_user,
                    "timestamp": conv.created_at.isoformat() if conv.created_at else None
                }
                for conv in recent
            ]
        except Exception as e:
            logger.error(f"Error retrieving recent conversations: {e}")
    
    # Get relevant tasks
    if include_tasks:
        try:
            # Get active tasks
            stmt = select(Task).where(
                Task.user_id == user_id,
                Task.status.in_(["pending", "in_progress"])
            ).order_by(
                Task.priority.desc(),
                Task.due_date.asc()
            ).limit(limit)
            
            result = await session.execute(stmt)
            tasks = result.scalars().all()
            
            context["relevant_tasks"] = [
                {
                    "id": task.id,
                    "title": task.title,
                    "pillar": task.pillar.value,
                    "priority": task.priority.value,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "status": task.status.value
                }
                for task in tasks
            ]
        except Exception as e:
            logger.error(f"Error retrieving relevant tasks: {e}")
    
    # Get user preferences
    try:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            context["user_preferences"] = {
                "work_start_hour": user.work_start_hour,
                "work_end_hour": user.work_end_hour,
                "timezone": user.timezone,
                "check_in_interval": user.check_in_interval
            }
    except Exception as e:
        logger.error(f"Error retrieving user preferences: {e}")
    
    return context


async def format_context_for_prompt(context: Dict[str, Any]) -> str:
    """
    Format context dictionary into a prompt-friendly string.
    
    Args:
        context: Context dictionary from get_context_for_ai
    
    Returns:
        Formatted string for AI prompt
    """
    parts = []
    
    # Recent conversations
    if context.get("recent_conversations"):
        parts.append("## Recent Conversation History:")
        for conv in context["recent_conversations"][:5]:  # Last 5
            role = "User" if conv["is_from_user"] else "Assistant"
            parts.append(f"{role}: {conv['text']}")
    
    # Relevant conversations (semantic matches)
    if context.get("relevant_conversations"):
        parts.append("\n## Relevant Past Conversations:")
        for conv in context["relevant_conversations"][:3]:  # Top 3
            parts.append(f"- {conv['text']}")
    
    # Active tasks
    if context.get("relevant_tasks"):
        parts.append("\n## Current Active Tasks:")
        for task in context["relevant_tasks"][:5]:  # Top 5
            due_str = f" (due: {task['due_date']})" if task.get("due_date") else ""
            parts.append(f"- [{task['priority'].upper()}] {task['title']}{due_str}")
    
    # User preferences
    if context.get("user_preferences"):
        prefs = context["user_preferences"]
        parts.append(f"\n## User Preferences:")
        parts.append(f"Work hours: {prefs.get('work_start_hour', 8)}:00 - {prefs.get('work_end_hour', 20)}:00")
        parts.append(f"Timezone: {prefs.get('timezone', 'UTC')}")
    
    return "\n".join(parts)

