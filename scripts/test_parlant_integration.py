"""
Test script for Parlant integration.
Tests agent creation, guidelines, tools, and message processing.
"""
import asyncio
import logging
import sys
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_parlant_import():
    """Test if Parlant can be imported."""
    try:
        import parlant.sdk as p
        logger.info("✅ Parlant SDK imported successfully")
        logger.info(f"   Parlant version: {p.__version__ if hasattr(p, '__version__') else 'unknown'}")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import Parlant: {e}")
        logger.error("   Run: pip install parlant")
        return False


async def test_session_creation():
    """Test creating a Parlant session."""
    try:
        from agents_parlant.agent import get_or_create_session
        
        # Test user ID
        test_user_id = 12345
        
        logger.info(f"Creating session for test user {test_user_id}...")
        session = await get_or_create_session(test_user_id)
        
        logger.info("✅ Session created successfully")
        logger.info(f"   Session type: {type(session)}")
        logger.info(f"   Session ID: {session.id if hasattr(session, 'id') else 'N/A'}")
        
        # Check session attributes
        logger.info(f"   Session attributes: {[attr for attr in dir(session) if not attr.startswith('_')][:10]}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create session: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def test_tools():
    """Test that tools are properly defined."""
    try:
        from agents_parlant import tools
        
        # Check if tools are defined
        tool_functions = [
            tools.get_user_tasks,
            tools.create_user_task,
            tools.get_calendar_events,
            tools.create_calendar_event,
            tools.get_user_info,
        ]
        
        logger.info(f"✅ Found {len(tool_functions)} tools")
        for tool in tool_functions:
            tool_name = getattr(tool, '__name__', str(tool))
            logger.info(f"   - {tool_name}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import tools: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def test_message_processing():
    """Test processing a message through Parlant."""
    try:
        from agents_parlant.agent import process_message
        
        test_user_id = 12345
        test_message = "Show me my tasks"
        
        logger.info(f"Processing test message: '{test_message}'")
        logger.info("   (This may fail if Parlant API is different - that's okay)")
        
        response = await process_message(test_user_id, test_message)
        
        logger.info("✅ Message processed")
        logger.info(f"   Response: {response[:200]}...")
        
        return True
    except Exception as e:
        logger.warning(f"⚠️  Message processing test failed: {e}")
        logger.warning("   This might be due to Parlant API differences - check Parlant SDK docs")
        logger.warning("   The integration will try multiple API patterns at runtime")
        return False


async def test_telegram_adapter():
    """Test Telegram adapter import."""
    try:
        from agents_parlant.telegram_adapter import handle_message_with_parlant
        logger.info("✅ Telegram adapter imported successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import Telegram adapter: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def test_configuration():
    """Test configuration."""
    try:
        use_parlant = getattr(settings, 'use_parlant', False)
        logger.info(f"✅ Configuration loaded")
        logger.info(f"   USE_PARLANT: {use_parlant}")
        if not use_parlant:
            logger.info("   💡 Set USE_PARLANT=true in .env to enable Parlant")
        return True
    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Testing Parlant Integration")
    logger.info("=" * 60)
    logger.info("")
    
    results = []
    
    # Test 1: Import
    logger.info("Test 1: Parlant SDK Import")
    logger.info("-" * 60)
    results.append(await test_parlant_import())
    logger.info("")
    
    if not results[0]:
        logger.error("Cannot continue - Parlant SDK not available")
        logger.error("Install with: pip install parlant")
        return
    
    # Test 2: Configuration
    logger.info("Test 2: Configuration")
    logger.info("-" * 60)
    results.append(await test_configuration())
    logger.info("")
    
    # Test 3: Tools
    logger.info("Test 3: Tools Definition")
    logger.info("-" * 60)
    results.append(await test_tools())
    logger.info("")
    
    # Test 4: Session Creation
    logger.info("Test 4: Session Creation")
    logger.info("-" * 60)
    results.append(await test_session_creation())
    logger.info("")
    
    # Test 5: Telegram Adapter
    logger.info("Test 5: Telegram Adapter")
    logger.info("-" * 60)
    results.append(await test_telegram_adapter())
    logger.info("")
    
    # Test 6: Message Processing (may fail - that's okay)
    logger.info("Test 6: Message Processing")
    logger.info("-" * 60)
    results.append(await test_message_processing())
    logger.info("")
    
    # Summary
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    logger.info(f"Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("✅ All tests passed!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Set USE_PARLANT=true in .env")
        logger.info("2. Restart your bot")
        logger.info("3. Send a test message on Telegram")
    elif passed >= total - 1:
        logger.info("⚠️  Most tests passed")
        logger.info("   Message processing may need Parlant SDK API adjustments")
        logger.info("   The integration will try multiple API patterns at runtime")
    else:
        logger.info("❌ Some tests failed")
        logger.info("   Check the errors above and fix issues")
    
    logger.info("")
    logger.info("For more info, see: docs/PARLANT_INTEGRATION.md")


if __name__ == "__main__":
    asyncio.run(main())

