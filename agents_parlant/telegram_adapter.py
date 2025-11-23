"""
Telegram adapter for Parlant integration.
Bridges Telegram bot messages with Parlant agent processing.
"""
import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from agents_parlant.agent import process_message as parlant_process_message

logger = logging.getLogger(__name__)


async def handle_message_with_parlant(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle Telegram message using Parlant agent.
    
    This is the main entry point for processing messages through Parlant.
    It bridges Parlant agents with Telegram handlers.
    
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
        
        logger.info(f"Parlant Integration: Processing message from user {user.id}: '{text[:100]}'")
        
        # Process message through Parlant
        response = await parlant_process_message(
            user_id=user.id,
            message=text
        )
        
        logger.info(f"Parlant Integration: Response length={len(response)}")
        
        # Send response to user
        if response:
            await update.message.reply_text(response, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "I received your message. How can I help you today?"
            )
        
    except Exception as e:
        logger.error(f"Parlant Integration: Fatal error: {e}", exc_info=True)
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Fallback to LangGraph or natural language handler
        try:
            logger.info("Falling back to LangGraph handler")
            from agents_langgraph.integration import handle_message_with_langgraph
            await handle_message_with_langgraph(update, context)
            return
        except Exception as langgraph_error:
            logger.warning(f"LangGraph fallback also failed: {langgraph_error}")
            # Final fallback to natural language handler
            try:
                from telegram_bot.handlers.start import handle_natural_language
                await handle_natural_language(update, context)
                return
            except Exception as nl_error:
                logger.error(f"All handlers failed: {nl_error}")
        
        # Try to send error message to user
        try:
            await update.message.reply_text(
                "⚠️ I encountered an error processing your message.\n\n"
                "Please try again or use /help for assistance.\n\n"
                "If this persists, the issue has been logged."
            )
        except Exception:
            pass  # Failed to send message

