#!/usr/bin/env python3
"""
Run bot with maximum debugging output to catch errors.
"""
import sys
import os
import logging
import asyncio
from datetime import datetime

# Set up very verbose logging BEFORE any other imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_debug.log', mode='w', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger.info("=" * 80)
logger.info("🔍 STARTING BOT WITH FULL DEBUGGING")
logger.info("=" * 80)
logger.info(f"Time: {datetime.now()}")
logger.info(f"Python: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info("=" * 80)

# Test imports step by step
try:
    logger.info("Step 1: Importing config...")
    from config import settings
    logger.info("✅ Config imported successfully")
    logger.info(f"   Database URL: {settings.database_url[:60]}...")
    logger.info(f"   Bot token: {settings.telegram_bot_token[:20]}..." if settings.telegram_bot_token else "   Bot token: NOT SET")
except Exception as e:
    logger.error(f"❌ Config import failed: {e}", exc_info=True)
    sys.exit(1)

try:
    logger.info("Step 2: Initializing database connection...")
    from database.connection import AsyncSessionLocal, _init_engines
    _init_engines()
    logger.info("✅ Database connection initialized")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
    sys.exit(1)

try:
    logger.info("Step 3: Importing bot modules...")
    from telegram_bot.bot import create_application, setup_handlers
    from telegram_bot.handlers import start
    logger.info("✅ Bot modules imported successfully")
except Exception as e:
    logger.error(f"❌ Bot module import failed: {e}", exc_info=True)
    sys.exit(1)

# Test database query
async def test_db():
    logger.info("Step 4: Testing database query...")
    try:
        from database.connection import AsyncSessionLocal
        from database.models import User
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            stmt = select(User).limit(1)
            result = await session.execute(stmt)
            users = result.scalars().all()
            logger.info(f"✅ Database query successful (found {len(users)} users)")
            return True
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}", exc_info=True)
        return False

async def main():
    """Run bot with full error handling."""
    logger.info("=" * 80)
    logger.info("🚀 STARTING BOT")
    logger.info("=" * 80)
    
    # Test database first
    db_ok = await test_db()
    if not db_ok:
        logger.error("Database test failed. Exiting.")
        return
    
    try:
        # Create application
        logger.info("Creating bot application...")
        application = create_application()
        logger.info("✅ Application created")
        
        # Setup handlers
        logger.info("Setting up handlers...")
        setup_handlers(application)
        logger.info("✅ Handlers set up")
        
        # Initialize bot
        logger.info("Initializing bot...")
        await application.initialize()
        logger.info("✅ Bot initialized")
        
        # Start polling
        logger.info("=" * 80)
        logger.info("✅ BOT IS READY - Starting polling...")
        logger.info("=" * 80)
        logger.info("Send /start in Telegram to test!")
        logger.info("All errors will be logged below:")
        logger.info("=" * 80)
        
        await application.start()
        await application.updater.start_polling(
            allowed_updates=['message', 'callback_query'],
            drop_pending_updates=True
        )
        
        # Keep running
        logger.info("Bot is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 80)
        logger.info("🛑 SHUTTING DOWN BOT")
        logger.info("=" * 80)
        try:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
            logger.info("✅ Bot stopped cleanly")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ FATAL ERROR IN BOT")
        logger.error("=" * 80)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("Full traceback:")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

