"""
Main Telegram bot instance and handler registration.
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import settings

logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors with improved logging and user-friendly messages."""
    from telegram.error import Conflict, RetryAfter, TimedOut, NetworkError
    
    error = context.error
    error_type = error.__class__.__name__ if hasattr(error, '__class__') else 'Unknown'
    
    # Add user context to Sentry if available
    if update and update.effective_user:
        try:
            import sentry_sdk
            sentry_sdk.set_user({
                "id": update.effective_user.id,
                "username": update.effective_user.username,
                "first_name": update.effective_user.first_name,
            })
            # Add chat context
            if update.effective_chat:
                sentry_sdk.set_context("chat", {
                    "id": update.effective_chat.id,
                    "type": update.effective_chat.type,
                })
        except Exception:
            pass  # Don't fail if Sentry is not available
    
    # Handle specific Telegram errors
    if isinstance(error, Conflict):
        logger.error(f"⚠️ CONFLICT: Another bot instance is running! Please stop it first.")
        logger.error(f"   Error: {error}")
        logger.error("   Solution: Stop any other running instances or deployed bot.")
        # Don't try to send message to user for Conflict errors (they're internal)
        return
    
    if isinstance(error, RetryAfter):
        logger.warning(f"Rate limited. Retry after {error.retry_after} seconds.")
        return
    
    if isinstance(error, (TimedOut, NetworkError)):
        logger.warning(f"Network error: {error}. Will retry automatically.")
        return
    
    # Log other errors with full traceback
    logger.error("=" * 80)
    logger.error(f"❌ EXCEPTION in bot handler!")
    logger.error(f"Error type: {error_type}")
    logger.error(f"Error message: {str(error)}")
    logger.error("Full traceback:")
    import traceback
    logger.error(traceback.format_exc())
    logger.error("=" * 80)
    
    # Determine error category for user-friendly message
    from edge_cases.guardrails import format_user_friendly_error
    
    error_category = "validation_error"
    error_context = {"details": ""}
    
    if isinstance(error, ValueError):
        error_category = "validation_error"
        error_context["details"] = str(error) if str(error) else "Invalid input format"
    elif isinstance(error, ConnectionError):
        error_category = "database_error"
    elif isinstance(error, TimeoutError):
        error_category = "validation_error"
        error_context["details"] = "The operation took too long"
    elif isinstance(error, KeyError):
        error_category = "validation_error"
        error_context["details"] = "Missing required information"
    elif "database" in str(error).lower() or "sql" in str(error).lower():
        error_category = "database_error"
    elif "llm" in str(error).lower() or "openai" in str(error).lower() or "gemini" in str(error).lower():
        error_category = "llm_error"
    elif "calendar" in str(error).lower():
        error_category = "calendar_error"
    elif "greenlet" in str(error).lower():
        error_category = "dependency_error"
    
    # Handle greenlet/dependency errors specifically
    error_str = str(error).lower()
    is_greenlet_error = "greenlet" in error_str or isinstance(error, ImportError) and "greenlet" in error_str
    
    if is_greenlet_error:
        # Greenlet error - provide specific message
        user_message = (
            "⚠️ **Error: Missing Dependency**\n\n"
            "The bot requires the 'greenlet' library to function properly.\n\n"
            "**This is a system configuration issue.**\n\n"
            "The bot administrator needs to:\n"
            "1. Install greenlet: `pip install greenlet`\n"
            "2. Restart the bot\n\n"
            "Please contact support if this issue persists."
        )
        # Don't format with generic error handler for dependency errors
    else:
        # Format user-friendly error message following agent persona
        user_message = format_user_friendly_error(
            error_category,
            str(error),
            error_context
        )
        
        # Admit mistake and provide next steps (agent persona - Error Handling guardrails)
        user_message = (
            f"I encountered an error while processing your request. "
            f"{user_message}\n\n"
            f"**What you can do:**\n"
            f"- Try again in a moment\n"
            f"- Use /help to see available commands\n"
            f"- If the problem persists, please let me know"
        )
    
    # Send error message (handlers should suppress their own messages for ImportError)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(user_message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")


def create_application() -> Application:
    """Create and configure Telegram bot application."""
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Register handlers (will be imported from handlers module)
    # from telegram_bot.handlers import start, tasks, calendar, settings_handler, checkins
    
    return application


def setup_handlers(application: Application) -> None:
    """Set up all command and message handlers."""
    # Import handlers
    from telegram_bot.handlers import start, tasks, calendar_handler, settings_handler
    
    # Command handlers
    application.add_handler(CommandHandler("start", start.start_command))
    application.add_handler(CommandHandler("help", start.help_command))
    application.add_handler(CommandHandler("settings", settings_handler.settings_command))
    application.add_handler(CommandHandler("tasks", tasks.tasks_command))
    application.add_handler(CommandHandler("calendar", calendar_handler.calendar_command))
    application.add_handler(CommandHandler("sync_calendar", calendar_handler.sync_calendar_command))
    
    # Insights handler (adaptive learning)
    try:
        from telegram_bot.handlers import insights_handler
        application.add_handler(CommandHandler("insights", insights_handler.insights_command))
        logger.info("Insights handler registered")
    except Exception as e:
        logger.warning(f"Could not register insights handler: {e}")
    
    # Prioritization handler (optional - may fail due to LangChain/Pydantic compatibility)
    try:
        from telegram_bot.handlers import prioritization
        application.add_handler(CommandHandler("prioritize", prioritization.prioritize_command))
        logger.info("Prioritization handler registered")
    except Exception as e:
        logger.warning(f"Could not register prioritization handler: {e}")
        logger.warning("Bot will continue without /prioritize command")
    
    # Message handlers (natural language)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        start.handle_message
    ))
    
    # Callback query handlers (inline keyboard buttons)
    try:
        from telegram_bot.handlers import callbacks
        from telegram.ext import CallbackQueryHandler
        application.add_handler(CallbackQueryHandler(callbacks.handle_callback_query))
        logger.info("Callback query handler registered")
    except Exception as e:
        logger.warning(f"Could not register callback query handler: {e}")
    
    logger.info("Handlers registered")

