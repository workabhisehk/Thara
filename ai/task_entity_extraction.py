"""
Enhanced task entity extraction with AI according to COMPREHENSIVE_PLAN.md
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from ai.langchain_setup import get_llm, get_fallback_llm
from ai.prompts import TASK_ENTITY_EXTRACTION_PROMPT
from memory.context_retrieval import get_context_for_ai, format_context_for_prompt
from database.connection import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def extract_task_entities(
    user_message: str,
    user_id: int,
    session=None
) -> Dict[str, Any]:
    """
    Extract task-related entities from user message.
    
    Args:
        user_message: User's message text
        user_id: User ID
        session: Database session (optional)
    
    Returns:
        Dictionary with extracted entities:
        {
            "task_title": str,
            "priority": Optional[str],
            "due_date": Optional[str],
            "estimated_duration": Optional[int],  # minutes
            "description": Optional[str],
            "pillar": Optional[str],
            "confidence": float
        }
    """
    # Get context
    if session:
        context = await get_context_for_ai(session, user_id, user_message)
        context_str = format_context_for_prompt(context)
    else:
        async with AsyncSessionLocal() as session:
            context = await get_context_for_ai(session, user_id, user_message)
            context_str = format_context_for_prompt(context)
    
    # Build prompt
    prompt = TASK_ENTITY_EXTRACTION_PROMPT.format_messages(
        message=user_message,
        context=context_str
    )
    
    # Get LLM response
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response.content)
            
            # Parse and normalize entities
            entities = {
                "task_title": result.get("task_title") or "",
                "priority": result.get("priority", "").lower() if result.get("priority") else None,
                "due_date": parse_due_date(result.get("due_date")) if result.get("due_date") else None,
                "estimated_duration": parse_duration(result.get("estimated_duration")) if result.get("estimated_duration") else None,
                "description": result.get("description") or None,
                "pillar": result.get("pillar", "").lower() if result.get("pillar") else None,
                "confidence": float(result.get("confidence", 0.7))  # Explicitly convert to float for consistency
            }
            
            return entities
            
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse JSON from LLM: {e}")
            # Fallback: Try to extract task title manually
            return {
                "task_title": extract_title_fallback(user_message),
                "priority": None,
                "due_date": None,
                "estimated_duration": None,
                "description": None,
                "pillar": None,
                "confidence": 0.5
            }
            
    except Exception as e:
        logger.error(f"Error extracting task entities: {e}")
        # Try fallback
        try:
            fallback_llm = get_fallback_llm()
            if fallback_llm:
                response = fallback_llm.invoke(prompt)
                result = json.loads(response.content)
                # Normalize priority and pillar to lowercase to match main path behavior
                return {
                    "task_title": result.get("task_title") or extract_title_fallback(user_message),
                    "priority": result.get("priority", "").lower() if result.get("priority") else None,
                    "due_date": parse_due_date(result.get("due_date")) if result.get("due_date") else None,
                    "estimated_duration": parse_duration(result.get("estimated_duration")) if result.get("estimated_duration") else None,
                    "description": result.get("description"),
                    "pillar": result.get("pillar", "").lower() if result.get("pillar") else None,
                    "confidence": 0.6
                }
        except Exception as e2:
            logger.error(f"Fallback LLM also failed: {e2}")
        
        # Final fallback
        return {
            "task_title": extract_title_fallback(user_message),
            "priority": None,
            "due_date": None,
            "estimated_duration": None,
            "description": None,
            "pillar": None,
            "confidence": 0.3
        }


def extract_title_fallback(message: str) -> str:
    """Fallback title extraction if AI fails."""
    # Remove common prefixes
    prefixes = ["add task", "create task", "new task", "task", "add", "create", "new"]
    
    # Strip the message first to handle leading whitespace correctly
    message_stripped = message.strip()
    message_lower = message_stripped.lower()
    
    for prefix in prefixes:
        if message_lower.startswith(prefix):
            # Slice from the stripped message using the prefix length
            message_stripped = message_stripped[len(prefix):].strip(": ").strip()
            break
    
    # Take first 200 characters
    return message_stripped[:200].strip()


def parse_due_date(date_str: str) -> Optional[datetime]:
    """Parse due date from string using dateutil."""
    if not date_str:
        return None
    
    try:
        date_str_lower = date_str.lower().strip()
        now = datetime.utcnow()
        
        # Handle relative dates
        if date_str_lower in ["today", "tdy"]:
            return now.replace(hour=23, minute=59, second=0, microsecond=0)
        elif date_str_lower in ["tomorrow", "tmr", "tmrw"]:
            tomorrow = now + relativedelta(days=1)
            return tomorrow.replace(hour=23, minute=59, second=0, microsecond=0)
        elif date_str_lower.startswith("next week"):
            return now + relativedelta(weeks=1, weekday=0)  # Next Monday
        elif date_str_lower.startswith("next month"):
            return now + relativedelta(months=1)
        
        # Parse with dateutil
        parsed_date = date_parser.parse(date_str, default=now)
        return parsed_date
        
    except Exception as e:
        logger.warning(f"Could not parse date '{date_str}': {e}")
        return None


def parse_duration(duration_str: Any) -> Optional[int]:
    """Parse duration to minutes."""
    if isinstance(duration_str, (int, float)):
        # If already in minutes
        if duration_str > 1000:  # Likely in seconds
            return int(duration_str / 60)
        return int(duration_str)
    
    if not duration_str or not isinstance(duration_str, str):
        return None
    
    import re
    
    duration_str = duration_str.lower().strip()
    
    # Pattern: "2 hours" or "2h"
    hour_pattern = r'(\d+(?:\.\d+)?)\s*(?:hours?|h)'
    hour_match = re.search(hour_pattern, duration_str)
    hours = float(hour_match.group(1)) if hour_match else 0
    
    # Pattern: "30 minutes" or "30m"
    min_pattern = r'(\d+)\s*(?:minutes?|mins?|m)'
    min_match = re.search(min_pattern, duration_str)
    minutes = int(min_match.group(1)) if min_match else 0
    
    total_minutes = int(hours * 60) + minutes
    
    return total_minutes if total_minutes > 0 else None

