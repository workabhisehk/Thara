"""
Natural language understanding and intent extraction.
"""
import logging
import json
from typing import Dict, Any, Optional
from ai.langchain_setup import get_llm, get_fallback_llm
from ai.prompts import INTENT_EXTRACTION_PROMPT
from memory.context_retrieval import get_context_for_ai, format_context_for_prompt
from database.connection import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def extract_intent(
    user_message: str,
    user_id: int,
    session=None
) -> Dict[str, Any]:
    """
    Extract intent and entities from user message.
    
    Args:
        user_message: User's message text
        user_id: User ID
        session: Database session (optional)
    
    Returns:
        Dictionary with intent and entities
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
    prompt = INTENT_EXTRACTION_PROMPT.format_messages(
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
            return {
                "intent": result.get("intent", "unknown"),
                "entities": result.get("entities", {}),
                "confidence": 0.8
            }
        except json.JSONDecodeError:
            # Fallback parsing
            return {
                "intent": "general",
                "entities": {"message": user_message},
                "confidence": 0.5
            }
    except Exception as e:
        logger.error(f"Error extracting intent: {e}")
        # Try fallback
        try:
            fallback_llm = get_fallback_llm()
            if fallback_llm:
                response = fallback_llm.invoke(prompt)
                result = json.loads(response.content)
                return {
                    "intent": result.get("intent", "unknown"),
                    "entities": result.get("entities", {}),
                    "confidence": 0.7
                }
        except Exception as e2:
            logger.error(f"Fallback LLM also failed: {e2}")
        
        # Default fallback
        return {
            "intent": "general",
            "entities": {"message": user_message},
            "confidence": 0.3
        }


async def categorize_task(
    task_description: str,
    user_id: int,
    session=None
) -> str:
    """
    Categorize task into pillar using AI.
    
    Args:
        task_description: Task description
        user_id: User ID
        session: Database session (optional)
    
    Returns:
        Pillar name (work, education, projects, personal, other)
    """
    from ai.prompts import TASK_CATEGORIZATION_PROMPT
    
    # Get context
    if session:
        context = await get_context_for_ai(session, user_id, task_description)
        context_str = format_context_for_prompt(context)
    else:
        async with AsyncSessionLocal() as session:
            context = await get_context_for_ai(session, user_id, task_description)
            context_str = format_context_for_prompt(context)
    
    # Build prompt
    prompt = TASK_CATEGORIZATION_PROMPT.format_messages(
        task_description=task_description,
        context=context_str
    )
    
    # Get LLM response
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        pillar = response.content.strip().lower()
        
        # Validate pillar
        valid_pillars = ["work", "education", "projects", "personal", "other"]
        if pillar in valid_pillars:
            return pillar
        
        return "other"
    except Exception as e:
        logger.error(f"Error categorizing task: {e}")
        return "other"

