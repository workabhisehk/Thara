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

# Initialize Sentry for error tracking (before any other imports that might error)
if settings.sentry_dsn and settings.sentry_enabled:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    
    # Configure Sentry
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring
        traces_sample_rate=0.1,  # 10% of transactions for performance
        # Enable profiling (optional, requires sentry-sdk[fastapi])
        profiles_sample_rate=0.1,
        # Set environment
        environment=settings.environment,
        # Integrations
        integrations=[
            LoggingIntegration(
                level=logging.INFO,        # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            ),
            SqlalchemyIntegration(),
            AsyncioIntegration(),
        ],
        # Release tracking (useful for deployments)
        # release="bot@1.0.0",
        # Filter out some noisy logs
        ignore_errors=[
            KeyboardInterrupt,
            SystemExit,
        ],
        # Add user context to errors
        before_send=lambda event, hint: event,
    )
    logging.getLogger(__name__).info("✅ Sentry initialized for error tracking")

# Configure logging with detailed output
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,  # Force DEBUG level to see all errors
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)
# Reduce noise from some verbose libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


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
    try:
        from scheduler.jobs import init_scheduler
        await init_scheduler()
        logger.info("✅ Scheduler initialized successfully")
    except Exception as e:
        logger.error(f"❌ Could not initialize scheduler: {e}")
        logger.error("Bot will continue without scheduled jobs (check-ins, reminders, etc.)")
        logger.error("You can still use all bot commands manually")
        import traceback
        logger.error(traceback.format_exc())
    
    # Test opening message - "Hi" when bot starts
    logger.info("")
    logger.info("=" * 60)
    logger.info("👋 Hi! Bot is running and ready!")
    logger.info("=" * 60)
    logger.info("Bot initialized and ready")
    
    # Send "Hi" message to all registered users (for testing)
    try:
        await send_startup_message(application)
    except Exception as e:
        logger.warning(f"Could not send startup messages: {e}")


async def send_startup_message(application: Application) -> None:
    """Send 'Hi' message to registered users when bot starts."""
    from database.connection import AsyncSessionLocal
    from database.models import User
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        # Get all active users
        stmt = select(User).where(User.is_active == True)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        if not users:
            logger.info("No registered users yet. Send /start to the bot to get started!")
            return
        
        logger.info(f"Sending startup 'Hi' message to {len(users)} registered user(s)...")
        
        for user in users:
            try:
                await application.bot.send_message(
                    chat_id=user.telegram_id,
                    text="👋 Hi! Bot is running and ready!"
                )
                logger.info(f"✅ Sent startup message to user {user.telegram_id} ({user.first_name})")
            except Exception as e:
                logger.warning(f"Could not send startup message to user {user.telegram_id}: {e}")


async def post_shutdown(application: Application) -> None:
    """Cleanup on shutdown."""
    # Shutdown scheduler (if it was initialized)
    try:
        from scheduler.jobs import shutdown_scheduler
        await shutdown_scheduler()
    except Exception as e:
        logger.warning(f"Could not shutdown scheduler: {e}")
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
        logger.error("=" * 80)
        logger.error("❌ FATAL ERROR STARTING BOT")
        logger.error("=" * 80)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("Full traceback:")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        logger.error("Check the logs above for the exact error!")
        sys.exit(1)


if __name__ == "__main__":
    main()

