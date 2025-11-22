"""
Context-aware response generation according to COMPREHENSIVE_PLAN.md and AGENT_PERSONA_AND_EVALS.md
"""
import logging
from typing import Dict, Any, Optional
from ai.langchain_setup import get_llm, get_fallback_llm
from ai.prompts import CONTEXT_RESPONSE_PROMPT
from memory.context_retrieval import get_context_for_ai, format_context_for_prompt
from database.connection import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def generate_context_aware_response(
    user_message: str,
    user_id: int,
    intent: str,
    entities: Dict[str, Any],
    session=None
) -> str:
    """
    Generate a personalized, context-aware response to user message.
    Aligned with agent persona from AGENT_PERSONA_AND_EVALS.md.
    
    Args:
        user_message: User's message text
        user_id: User ID
        intent: Extracted intent
        entities: Extracted entities
        session: Database session (optional)
    
    Returns:
        Generated response text
    """
    # Get comprehensive context
    if session:
        context = await get_context_for_ai(session, user_id, user_message)
        context_str = format_context_for_prompt(context)
    else:
        async with AsyncSessionLocal() as session:
            context = await get_context_for_ai(session, user_id, user_message)
            context_str = format_context_for_prompt(context)
    
    # Build prompt with persona and context (SYSTEM_PROMPT is already included in CONTEXT_RESPONSE_PROMPT)
    messages = CONTEXT_RESPONSE_PROMPT.format_messages(
        message=user_message,
        context=context_str
    )
    
    # Get LLM response
    try:
        llm = get_llm()
        response = llm.invoke(messages)
        
        response_text = response.content.strip()
        
        # Ensure response follows persona guidelines
        # - Concise (<200 words)
        # - Action-oriented
        # - Non-judgmental
        if len(response_text.split()) > 200:
            # Truncate if too long (can be improved later)
            words = response_text.split()[:200]
            response_text = " ".join(words) + "..."
        
        logger.debug(f"Generated context-aware response for user {user_id}")
        return response_text
        
    except Exception as e:
        logger.error(f"Error generating context-aware response: {e}")
        # Try fallback
        try:
            fallback_llm = get_fallback_llm()
            if fallback_llm:
                response = fallback_llm.invoke(messages)
                return response.content.strip()
        except Exception as e2:
            logger.error(f"Fallback LLM also failed: {e2}")
        
        # Default fallback response
        return (
            "I understand your message. I'm processing it with context from our past interactions.\n\n"
            "For now, please use /help to see available commands, or be more specific about what you need."
        )

