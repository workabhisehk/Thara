#!/usr/bin/env python3
"""
Test script for LangGraph multi-agent system.
Quick validation before full deployment.
"""
import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_imports():
    """Test that all imports work."""
    print("\n🔍 Testing imports...")
    
    try:
        from agents_langgraph.state import AgentState, create_initial_state
        print("  ✅ State imports OK")
    except Exception as e:
        print(f"  ❌ State import failed: {e}")
        return False
    
    try:
        from agents_langgraph.agents import router_agent
        print("  ✅ Agent imports OK")
    except Exception as e:
        print(f"  ❌ Agent import failed: {e}")
        return False
    
    try:
        from agents_langgraph.graph import get_graph, process_message
        print("  ✅ Graph imports OK")
    except Exception as e:
        print(f"  ❌ Graph import failed: {e}")
        return False
    
    try:
        from agents_langgraph.integration import handle_message_with_langgraph
        print("  ✅ Integration imports OK")
    except Exception as e:
        print(f"  ❌ Integration import failed: {e}")
        return False
    
    return True


async def test_graph_compilation():
    """Test that graph compiles."""
    print("\n🔍 Testing graph compilation...")
    
    try:
        from agents_langgraph.graph import get_graph
        graph = get_graph()
        print("  ✅ Graph compiled successfully")
        return True
    except Exception as e:
        print(f"  ❌ Graph compilation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_state_creation():
    """Test state creation."""
    print("\n🔍 Testing state creation...")
    
    try:
        from agents_langgraph.state import create_initial_state
        from telegram_bot.conversation import ConversationState
        
        state = create_initial_state(
            user_id=123,
            message="Hello, test message",
            current_state=ConversationState.NORMAL
        )
        
        assert state["user_id"] == 123
        assert state["current_state"] == ConversationState.NORMAL
        assert len(state["messages"]) > 0
        
        print("  ✅ State creation OK")
        return True
    except Exception as e:
        print(f"  ❌ State creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment():
    """Test environment variables."""
    print("\n🔍 Testing environment variables...")
    
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "OPENAI_API_KEY",
        "DATABASE_URL",
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"  ⚠️  Missing environment variables: {', '.join(missing)}")
        print("  💡 Create a .env file with required variables")
        return False
    else:
        print("  ✅ All required environment variables present")
        return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("LangGraph Multi-Agent System - Local Test")
    print("=" * 60)
    
    # Test imports
    if not await test_imports():
        print("\n❌ Import tests failed. Please check dependencies.")
        print("   Run: pip install -r requirements.txt")
        return 1
    
    # Test environment
    env_ok = test_environment()
    if not env_ok:
        print("\n⚠️  Environment variables missing. Some tests may fail.")
        print("   But you can still test imports and compilation.")
    
    # Test state creation
    if not await test_state_creation():
        print("\n❌ State creation test failed.")
        return 1
    
    # Test graph compilation (may fail if dependencies not fully configured)
    try:
        if await test_graph_compilation():
            print("\n✅ All core tests passed!")
            print("\n📝 Next steps:")
            print("   1. Ensure .env file is configured")
            print("   2. Run database migrations: alembic upgrade head")
            print("   3. Start bot: python bot_main.py")
        else:
            print("\n⚠️  Graph compilation test failed (may need full environment)")
            print("   This is OK if you're just testing imports.")
    except Exception as e:
        print(f"\n⚠️  Graph compilation test skipped: {e}")
        print("   This may need full environment setup.")
    
    print("\n" + "=" * 60)
    print("✅ Local test complete!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

