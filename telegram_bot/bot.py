"""
Main Telegram bot instance and handler registration.
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import settings

logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, I encountered an error. Please try again or use /help for assistance."
        )


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
    
    # Message handlers (natural language)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        start.handle_message
    ))
    
    logger.info("Handlers registered")

