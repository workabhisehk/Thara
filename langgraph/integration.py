"""
Integration layer between LangGraph and Telegram handlers.
Bridges the LangGraph multi-agent system with existing Telegram bot handlers.
"""
import logging
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes
from langgraph.graph import process_message as langgraph_process_message
from telegram_bot.conversation import ConversationState, set_conversation_state

logger = logging.getLogger(__name__)


async def handle_message_with_langgraph(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle Telegram message using LangGraph multi-agent system.
    
    This is the main entry point for processing messages through LangGraph.
    It bridges LangGraph agents with existing Telegram handlers.
    
    Args:
        update: Telegram Update object
        context: Telegram context
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
        
        logger.info(f"LangGraph Integration: Processing message from user {user.id}: '{text[:100]}'")
        
        # Serialize Telegram Update for LangGraph state
        telegram_update_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "message_id": update.message.message_id if update.message else None,
        }
        
        # Process message through LangGraph
        result = await process_message(
            user_id=user.id,
            message=text,
            telegram_update=telegram_update_data
        )
        
        # Get active agent and response
        active_agent = result.get("active_agent")
        response_text = result.get("response", "I received your message.")
        error = result.get("error")
        final_state = result.get("state", {})
        
        logger.info(f"LangGraph Integration: Agent={active_agent}, Response length={len(response_text)}")
        
        # Handle errors
        if error:
            logger.error(f"LangGraph Integration: Error: {error}")
            await update.message.reply_text(
                f"⚠️ I encountered an error processing your message.\n\n"
                f"Error: {error[:200]}\n\n"
                "Please try again or use /help for assistance."
            )
            return
        
        # Route to existing handlers based on active agent
        # This allows gradual migration - LangGraph routes, existing handlers execute
        if active_agent == "onboarding_agent":
            # Delegate to existing onboarding handler
            from telegram_bot.handlers.onboarding import handle_onboarding_message
            await handle_onboarding_message(update, context)
            return
        
        elif active_agent == "task_agent":
            # Delegate to existing task handler
            intent = final_state.get("intent")
            if intent in ["add_task", "create_task"]:
                # Natural language task creation
                from telegram_bot.handlers.natural_language_tasks import handle_natural_language_task_creation
                intent_result = {
                    "intent": intent,
                    "entities": final_state.get("entities", {}),
                    "confidence": final_state.get("confidence", 0.5)
                }
                await handle_natural_language_task_creation(update, context, intent_result)
            else:
                # Regular task operations
                from telegram_bot.handlers.tasks import tasks_command
                await tasks_command(update, context)
            return
        
        elif active_agent == "calendar_agent":
            # Delegate to existing calendar handler
            from telegram_bot.handlers.calendar_handler import calendar_command
            await calendar_command(update, context)
            return
        
        elif active_agent == "adaptive_learning_agent":
            # Delegate to existing insights handler
            from telegram_bot.handlers.insights_handler import insights_command
            await insights_command(update, context)
            return
        
        elif active_agent == "human":
            # Send clarification message
            clarification = final_state.get("clarification_message", response_text)
            await update.message.reply_text(clarification)
            return
        
        # Default: send response from LangGraph
        if response_text and response_text != "I received your message.":
            await update.message.reply_text(response_text)
        else:
            # Fallback to existing natural language handler
            from telegram_bot.handlers.start import handle_natural_language
            await handle_natural_language(update, context)
        
    except Exception as e:
        logger.error(f"LangGraph Integration: Fatal error: {e}", exc_info=True)
        try:
            await update.message.reply_text(
                "👋 I encountered an unexpected error.\n\n"
                "Please try again or use /help for assistance."
            )
        except Exception:
            pass  # Failed to send message

