#!/usr/bin/env python3
"""
Test onboarding flow to diagnose issues.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from telegram_bot.conversation import (
    ConversationState,
    get_conversation_state_async,
    get_conversation_context_async,
    set_conversation_state_async
)

async def test_onboarding_state():
    """Test onboarding state management."""
    print("Testing onboarding state management...")
    print("=" * 60)
    
    # Get a test user (use your telegram_id)
    test_telegram_id = 8230716061  # Replace with your telegram_id
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == test_telegram_id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            print(f"❌ User with telegram_id {test_telegram_id} not found")
            print("   Run /start in Telegram first to create the user")
            return
        
        print(f"✅ Found user: {db_user.first_name} (ID: {db_user.id})")
        print(f"   Onboarded: {db_user.is_onboarded}")
        print(f"   Preferred name: {db_user.preferred_name}")
        print(f"   DB conversation_state: {db_user.conversation_state}")
        print(f"   DB conversation_context: {db_user.conversation_context}")
        print()
        
        # Check async state
        state = await get_conversation_state_async(test_telegram_id)
        context = await get_conversation_context_async(test_telegram_id)
        
        print(f"Async state: {state}")
        print(f"Context data: {context.data}")
        print()
        
        # Check if state matches
        if db_user.conversation_state:
            db_state = ConversationState(db_user.conversation_state)
            if state != db_state:
                print(f"⚠️  State mismatch!")
                print(f"   DB state: {db_state}")
                print(f"   Async state: {state}")
                print()
                print("Fixing state...")
                await set_conversation_state_async(test_telegram_id, db_state)
                print("✅ State synced")
            else:
                print("✅ State matches between DB and async")
        else:
            print("⚠️  No state in database")
            if state != ConversationState.IDLE:
                print(f"   Setting state to match async: {state}")
                db_user.conversation_state = state.value
                await session.commit()
                print("✅ State saved to DB")
        
        print()
        print("Onboarding flow check:")
        if db_user.is_onboarded:
            print("✅ User is marked as onboarded")
        else:
            print("⚠️  User is NOT onboarded")
            print(f"   Current state: {state}")
            
            if state == ConversationState.ONBOARDING_NAME:
                print("   → Should be asking for name")
            elif state == ConversationState.ONBOARDING_PILLARS:
                print("   → Should be asking for pillars")
            elif state == ConversationState.ONBOARDING_WORK_HOURS:
                print("   → Should be asking for work hours")
            elif state == ConversationState.ONBOARDING_TIMEZONE:
                print("   → Should be asking for timezone")
            elif state in [ConversationState.IDLE, ConversationState.NORMAL]:
                print("   → User is in IDLE/NORMAL state but not onboarded")
                print("   → This might be the issue!")
                print()
                print("   Fixing: Setting state to ONBOARDING_NAME...")
                await set_conversation_state_async(test_telegram_id, ConversationState.ONBOARDING_NAME)
                print("   ✅ State set to ONBOARDING_NAME")
                print("   → Try sending /start again in Telegram")

if __name__ == "__main__":
    asyncio.run(test_onboarding_state())

