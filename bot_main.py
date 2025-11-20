"""
Telegram bot entry point.
Initializes and runs the Telegram bot with all handlers.
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import Application
from config import settings

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.log_level.upper())
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Initialize bot after startup."""
    # Initialize scheduler
    from scheduler.jobs import init_scheduler
    await init_scheduler()
    logger.info("Bot initialized and ready")


async def post_shutdown(application: Application) -> None:
    """Cleanup on shutdown."""
    # Shutdown scheduler
    from scheduler.jobs import shutdown_scheduler
    await shutdown_scheduler()
    logger.info("Bot shutting down")


def main():
    """Main function to run the bot."""
    from telegram_bot.bot import create_application, setup_handlers
    
    # Create application
    application = create_application()
    
    # Add post-init and post-shutdown handlers
    application.post_init = post_init
    application.post_shutdown = post_shutdown
    
    # Setup handlers
    setup_handlers(application)
    
    logger.info("Starting bot...")
    
    # Run the bot
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()

