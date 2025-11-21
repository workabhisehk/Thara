"""
Telegram bot entry point.
Initializes and runs the Telegram bot with all handlers.
"""
import asyncio
import logging
import sys
from telegram import Update
from telegram.ext import Application
from config import settings

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.log_level.upper())
)
logger = logging.getLogger(__name__)


def validate_environment_on_startup():
    """Validate environment variables before starting the bot."""
    try:
        from scripts.validate_environment import validate_environment
        is_valid, errors, warnings = validate_environment()
        
        if errors:
            logger.error("Environment validation failed!")
            for error in errors:
                logger.error(error)
            logger.error("Please check your .env file and ensure all required variables are set.")
            logger.error("Run 'python scripts/validate_environment.py' for details.")
            return False
        
        if warnings:
            logger.warning("Environment validation warnings:")
            for warning in warnings:
                logger.warning(warning)
        
        logger.info("✅ Environment validation passed")
        return True
    except Exception as e:
        logger.warning(f"Could not validate environment: {e}")
        logger.warning("Continuing anyway, but errors may occur if configuration is invalid")
        return True  # Don't block startup if validation fails


async def post_init(application: Application) -> None:
    """Initialize bot after startup."""
    # Initialize scheduler
    from scheduler.jobs import init_scheduler
    await init_scheduler()
    
    # Test opening message - "Hi" when bot starts
    logger.info("")
    logger.info("=" * 60)
    logger.info("👋 Hi! Bot is running and ready!")
    logger.info("=" * 60)
    logger.info("Bot initialized and ready")


async def post_shutdown(application: Application) -> None:
    """Cleanup on shutdown."""
    # Shutdown scheduler
    from scheduler.jobs import shutdown_scheduler
    await shutdown_scheduler()
    logger.info("Bot shutting down")


def main():
    """Main function to run the bot."""
    logger.info("=" * 60)
    logger.info("Starting AI Productivity Agent Bot")
    logger.info("=" * 60)
    
    # Validate environment on startup
    if not validate_environment_on_startup():
        logger.error("Startup aborted due to environment validation failure")
        sys.exit(1)
    
    from telegram_bot.bot import create_application, setup_handlers
    
    try:
        # Create application
        logger.info("Creating Telegram application...")
        application = create_application()
        
        # Add post-init and post-shutdown handlers
        application.post_init = post_init
        application.post_shutdown = post_shutdown
        
        # Setup handlers
        logger.info("Setting up handlers...")
        setup_handlers(application)
        
        logger.info("✅ Bot ready to start polling")
        logger.info("=" * 60)
        logger.info("👋 Hi! Starting bot...")
        logger.info("")
        
        # Run the bot
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error starting bot: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

