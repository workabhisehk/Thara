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
                "confidence": float(result.get("confidence", 0.7))
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
                    "confidence": float(result.get("confidence", 0.7))  # Extract from result for consistency
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
    session=None,
    available_pillars: list = None
) -> Dict[str, Any]:
    """
    Categorize task into pillar using AI with confidence scoring.
    Supports user's custom pillars.
    
    Args:
        task_description: Task description
        user_id: User ID
        session: Database session (optional)
        available_pillars: List of user's available pillars (predefined + custom)
    
    Returns:
        Dictionary with:
        {
            "pillar": str,  # pillar name
            "confidence": float,  # 0.0-1.0
            "reasoning": str  # brief explanation
        }
    """
    from ai.prompts import TASK_CATEGORIZATION_PROMPT
    from database.models import User
    from sqlalchemy import select
    
    # Get user's available pillars (predefined + custom from conversation context)
    if available_pillars is None:
        available_pillars = ["work", "education", "projects", "personal", "other"]
        # TODO: Get custom pillars from User model when custom_pillars field is added
    
    # Get context
    if session:
        context = await get_context_for_ai(session, user_id, task_description)
        context_str = format_context_for_prompt(context)
    else:
        async with AsyncSessionLocal() as session:
            context = await get_context_for_ai(session, user_id, task_description)
            context_str = format_context_for_prompt(context)
    
    # Format available pillars string
    pillars_str = ", ".join([p.capitalize() for p in available_pillars])
    
    # Build prompt
    prompt = TASK_CATEGORIZATION_PROMPT.format_messages(
        task_description=task_description,
        available_pillars=pillars_str,
        context=context_str
    )
    
    # Get LLM response
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response.content)
            pillar = result.get("pillar", "other").lower()
            confidence = float(result.get("confidence", 0.7))
            reasoning = result.get("reasoning", "")
            
            # Validate pillar is in available pillars
            if pillar not in [p.lower() for p in available_pillars]:
                pillar = "other"
                confidence = 0.5
            
            return {
                "pillar": pillar,
                "confidence": confidence,
                "reasoning": reasoning
            }
        except json.JSONDecodeError:
            # Fallback: Try to extract from text
            pillar = response.content.strip().lower()
            if pillar in [p.lower() for p in available_pillars]:
                return {
                    "pillar": pillar,
                    "confidence": 0.6,
                    "reasoning": "Extracted from text"
                }
            return {
                "pillar": "other",
                "confidence": 0.5,
                "reasoning": "Fallback to other"
            }
            
    except Exception as e:
        logger.error(f"Error categorizing task: {e}")
        # Try fallback LLM (consistent with extract_intent pattern)
        try:
            from ai.langchain_setup import get_fallback_llm
            fallback_llm = get_fallback_llm()
            if fallback_llm:
                logger.info("Attempting fallback LLM for task categorization")
                response = fallback_llm.invoke(prompt)
                # Parse JSON response
                try:
                    result = json.loads(response.content)
                    pillar = result.get("pillar", "other").lower()
                    confidence = float(result.get("confidence", 0.7))
                    reasoning = result.get("reasoning", "")
                    
                    # Validate pillar is in available pillars
                    if pillar not in [p.lower() for p in available_pillars]:
                        pillar = "other"
                        confidence = 0.5
                    
                    return {
                        "pillar": pillar,
                        "confidence": confidence,
                        "reasoning": reasoning or "Fallback LLM response"
                    }
                except json.JSONDecodeError:
                    # Fallback: Try to extract from text
                    pillar = response.content.strip().lower()
                    if pillar in [p.lower() for p in available_pillars]:
                        return {
                            "pillar": pillar,
                            "confidence": 0.6,
                            "reasoning": "Extracted from fallback LLM text"
                        }
        except Exception as e2:
            logger.error(f"Fallback LLM also failed: {e2}")
        
        # Default fallback (only if both main and fallback LLM failed)
        return {
            "pillar": "other",
            "confidence": 0.3,
            "reasoning": f"Error: {str(e)}"
        }

