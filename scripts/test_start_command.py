#!/usr/bin/env python3
"""
Test the exact /start command handler code path in the bot context.
This simulates how the bot actually runs.
"""
import sys
import os
import asyncio
import logging

# Setup logging to see errors
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import bot dependencies
from telegram.ext import ContextTypes
from telegram import Update, User as TelegramUser, Message, Chat
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
import traceback

# Mock update object
def create_mock_update(telegram_id=123456789, username="test_user", first_name="Test"):
    """Create a mock Update object for testing."""
    chat = Chat(id=telegram_id, type="private")
    user = TelegramUser(
        id=telegram_id,
        is_bot=False,
        first_name=first_name,
        username=username
    )
    message = Message(
        message_id=1,
        date=None,
        chat=chat,
        from_user=user,
        text="/start"
    )
    return Update(update_id=1, message=message)

async def test_start_handler():
    """Test the exact code from start_command handler."""
    print("=" * 60)
    print("Testing /start command handler code path...")
    print("=" * 60)
    print()
    
    # Create mock update
    update = create_mock_update()
    user = update.effective_user
    
    print(f"Testing with user:")
    print(f"  ID: {user.id}")
    print(f"  Username: {user.username}")
    print(f"  Name: {user.first_name}")
    print()
    
    try:
        print("Step 1: Creating database session...")
        async with AsyncSessionLocal() as session:
            print("  ✅ Session created")
            
            print("Step 2: Executing query to check if user exists...")
            stmt = select(User).where(User.telegram_id == user.id)
            print(f"  Query: {stmt}")
            
            result = await session.execute(stmt)
            print("  ✅ Query executed")
            
            db_user = result.scalar_one_or_none()
            print(f"  ✅ Query completed")
            print(f"  User exists in DB: {db_user is not None}")
            
            if db_user:
                print(f"  User is onboarded: {db_user.is_onboarded}")
            else:
                print("  User not found - would create new user")
            
            print()
            print("=" * 60)
            print("✅ SUCCESS! /start command handler code works!")
            print("=" * 60)
            return True
            
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR in /start handler!")
        print("=" * 60)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print()
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_start_handler())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

