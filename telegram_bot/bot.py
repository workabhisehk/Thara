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
    
    # Log other errors
    logger.error(f"Exception while handling an update: {error}", exc_info=error)
    logger.error(f"Error type: {error_type}")
    
    # Provide more specific error messages based on error type
    user_message = "Sorry, I encountered an error. Please try again or use /help for assistance."
    
    if isinstance(error, ValueError):
        user_message = f"⚠️ Invalid input: {str(error)}. Please check and try again."
    elif isinstance(error, ConnectionError):
        user_message = "⚠️ Connection error. Please try again in a moment."
    elif isinstance(error, TimeoutError):
        user_message = "⚠️ Request timed out. Please try again."
    elif isinstance(error, KeyError):
        user_message = "⚠️ Missing information. Please provide all required details."
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(user_message)
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
    
    # Prioritization handler
    from telegram_bot.handlers import prioritization
    application.add_handler(CommandHandler("prioritize", prioritization.prioritize_command))
    
    # Message handlers (natural language)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        start.handle_message
    ))
    
    logger.info("Handlers registered")

