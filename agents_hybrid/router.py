"""
Hybrid router that intelligently routes messages to Parlant or LangGraph
based on message complexity, intent, and conversation state.

This allows using both frameworks simultaneously:
- Parlant: Simple, direct operations (task CRUD, calendar queries)
- LangGraph: Complex workflows (onboarding, multi-step planning, multi-agent coordination)
"""
import logging
from typing import Dict, Any, Optional, Literal
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Simple intents that Parlant handles well
PARLANT_INTENTS = {
    "add_task",
    "create_task",
    "list_tasks",
    "get_tasks",
    "update_task",
    "complete_task",
    "delete_task",
    "get_calendar_events",
    "list_calendar",
    "schedule_event",
    "create_event",
    "query_calendar",
    "general",
    "greeting",
}

# Complex intents that benefit from LangGraph's multi-agent system
LANGGRAPH_INTENTS = {
    "onboarding",
    "complex_planning",
    "adaptive_learning",
    "insights",
    "weekly_review",
    "multi_step_task",
    "coordination",
}

# Keywords that suggest simple operations (Parlant)
SIMPLE_KEYWORDS = [
    "add task",
    "create task",
    "list tasks",
    "show tasks",
    "my tasks",
    "complete task",
    "done",
    "delete task",
    "remove task",
    "calendar",
    "schedule",
    "what's on",
    "events",
    "meetings",
]

# Keywords that suggest complex workflows (LangGraph)
COMPLEX_KEYWORDS = [
    "onboard",
    "setup",
    "configure",
    "plan",
    "review",
    "insights",
    "analytics",
    "learn",
    "adapt",
    "help me plan",
    "what should I",
]


async def route_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    conversation_state: Optional[str] = None,
    intent_result: Optional[Dict[str, Any]] = None,
) -> Literal["parlant", "langgraph"]:
    """
    Route a message to either Parlant or LangGraph based on complexity and intent.
    
    Args:
        update: Telegram Update object
        context: Telegram context
        conversation_state: Current conversation state
        intent_result: Extracted intent result (if available)
    
    Returns:
        "parlant" or "langgraph"
    """
    text = (update.message.text or "").lower().strip()
    user_id = update.effective_user.id if update.effective_user else None
    
    logger.info(f"Hybrid Router: Routing message for user {user_id}: '{text[:100]}'")
    
    # Rule 1: Onboarding always uses LangGraph (multi-step, stateful)
    if conversation_state and "onboarding" in conversation_state.lower():
        logger.info("Hybrid Router: Onboarding state detected → LangGraph")
        return "langgraph"
    
    # Rule 2: If intent is extracted, use it to route
    if intent_result:
        intent = intent_result.get("intent", "").lower()
        confidence = intent_result.get("confidence", 0.5)
        
        if intent in PARLANT_INTENTS and confidence > 0.6:
            logger.info(f"Hybrid Router: Simple intent '{intent}' (confidence: {confidence}) → Parlant")
            return "parlant"
        
        if intent in LANGGRAPH_INTENTS:
            logger.info(f"Hybrid Router: Complex intent '{intent}' → LangGraph")
            return "langgraph"
    
    # Rule 3: Check for simple operation keywords
    for keyword in SIMPLE_KEYWORDS:
        if keyword in text:
            logger.info(f"Hybrid Router: Simple keyword '{keyword}' detected → Parlant")
            return "parlant"
    
    # Rule 4: Check for complex workflow keywords
    for keyword in COMPLEX_KEYWORDS:
        if keyword in text:
            logger.info(f"Hybrid Router: Complex keyword '{keyword}' detected → LangGraph")
            return "langgraph"
    
    # Rule 5: Message length heuristic (very short = simple, very long = complex)
    if len(text) < 20:
        # Very short messages are usually simple queries
        logger.info("Hybrid Router: Short message → Parlant")
        return "parlant"
    elif len(text) > 200:
        # Long messages might be complex multi-step requests
        logger.info("Hybrid Router: Long message → LangGraph")
        return "langgraph"
    
    # Rule 6: Check for multi-part requests (containing "and", "then", "also", etc.)
    multi_part_indicators = [" and ", " then ", " also ", " next ", " after ", " before "]
    if any(indicator in text for indicator in multi_part_indicators):
        logger.info("Hybrid Router: Multi-part request detected → LangGraph")
        return "langgraph"
    
    # Default: Use Parlant for simpler, direct operations
    logger.info("Hybrid Router: Default → Parlant")
    return "parlant"


async def handle_message_hybrid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    conversation_state: Optional[str] = None,
) -> None:
    """
    Handle a message using hybrid routing between Parlant and LangGraph.
    
    This is the main entry point for hybrid mode.
    """
    try:
        user = update.effective_user
        text = update.message.text if update.message else ""
        
        if not text:
            await update.message.reply_text(
                "👋 Hi! I'm **Thara**, your productivity assistant.\n\n"
                "Please send me a text message, or use /help to see available commands."
            )
            return
        
        logger.info(f"Hybrid Mode: Processing message from user {user.id}: '{text[:100]}'")
        
        # Try to extract intent for better routing (optional, non-blocking)
        intent_result = None
        try:
            from ai.intent_extraction import extract_intent
            from database.models import User
            from database.connection import AsyncSessionLocal
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as session:
                stmt = select(User).where(User.telegram_id == user.id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()
                
                if db_user:
                    intent_result = await extract_intent(text, db_user.id, session)
                    logger.info(f"Hybrid Mode: Extracted intent: {intent_result.get('intent')} "
                              f"(confidence: {intent_result.get('confidence', 0.5):.2f})")
        except Exception as e:
            logger.debug(f"Hybrid Mode: Could not extract intent: {e}")
            # Continue without intent - router will use other heuristics
        
        # Route the message
        framework = await route_message(
            update,
            context,
            conversation_state=conversation_state,
            intent_result=intent_result
        )
        
        # Route to appropriate framework
        if framework == "parlant":
            logger.info("Hybrid Mode: Routing to Parlant")
            try:
                from agents_parlant.telegram_adapter import handle_message_with_parlant
                await handle_message_with_parlant(update, context)
                return
            except Exception as parlant_error:
                logger.warning(f"Hybrid Mode: Parlant failed: {parlant_error}, falling back to LangGraph")
                # Fall through to LangGraph
        
        # Use LangGraph (either because it was routed here, or as fallback)
        logger.info("Hybrid Mode: Routing to LangGraph")
        try:
            from agents_langgraph.integration import handle_message_with_langgraph
            await handle_message_with_langgraph(update, context)
            return
        except Exception as langgraph_error:
            logger.warning(f"Hybrid Mode: LangGraph failed: {langgraph_error}")
            # Final fallback to natural language handler
            from telegram_bot.handlers.start import handle_natural_language
            await handle_natural_language(update, context)
    
    except Exception as e:
        logger.error(f"Hybrid Mode: Fatal error: {e}", exc_info=True)
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Try to send error message to user
        try:
            await update.message.reply_text(
                "⚠️ I encountered an error processing your message.\n\n"
                "Please try again or use /help for assistance.\n\n"
                "If this persists, the issue has been logged."
            )
        except Exception:
            pass  # Failed to send message

