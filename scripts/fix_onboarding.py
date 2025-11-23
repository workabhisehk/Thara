#!/usr/bin/env python3
"""
Fix onboarding issues - reset user onboarding status or diagnose problems.
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
    set_conversation_state_async
)

async def reset_onboarding(telegram_id: int):
    """Reset user's onboarding status to test the flow."""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            print(f"❌ User with telegram_id {telegram_id} not found")
            return False
        
        print(f"Resetting onboarding for user: {db_user.first_name}")
        print(f"  Current status: onboarded={db_user.is_onboarded}, state={db_user.conversation_state}")
        
        # Reset onboarding
        db_user.is_onboarded = False
        db_user.conversation_state = ConversationState.ONBOARDING_NAME.value
        await session.commit()
        
        # Set state
        await set_conversation_state_async(telegram_id, ConversationState.ONBOARDING_NAME)
        
        print("✅ Onboarding reset!")
        print("  → User can now run /start to begin onboarding")
        return True

async def diagnose_onboarding(telegram_id: int):
    """Diagnose onboarding issues."""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            print(f"❌ User not found")
            return
        
        print("=" * 60)
        print("Onboarding Diagnosis")
        print("=" * 60)
        print(f"User: {db_user.first_name} (ID: {db_user.id})")
        print(f"Telegram ID: {db_user.telegram_id}")
        print(f"Is Onboarded: {db_user.is_onboarded}")
        print(f"Preferred Name: {db_user.preferred_name}")
        print(f"Work Hours: {db_user.work_start_hour}:00 - {db_user.work_end_hour}:00")
        print(f"Timezone: {db_user.timezone}")
        print(f"DB State: {db_user.conversation_state}")
        print(f"DB Context: {db_user.conversation_context}")
        print()
        
        # Check async state
        state = await get_conversation_state_async(telegram_id)
        print(f"Async State: {state}")
        print()
        
        # Issues found
        issues = []
        
        if db_user.is_onboarded and not db_user.preferred_name:
            issues.append("⚠️  User is onboarded but has no preferred name")
        
        if db_user.is_onboarded and db_user.work_start_hour == 8 and db_user.work_end_hour == 20:
            issues.append("⚠️  User has default work hours (might not have set them)")
        
        if db_user.conversation_state != state.value:
            issues.append(f"⚠️  State mismatch: DB={db_user.conversation_state}, Async={state.value}")
        
        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("✅ No obvious issues found")
        
        print()
        print("To test onboarding:")
        print("  1. Run: python scripts/fix_onboarding.py reset <telegram_id>")
        print("  2. Then send /start in Telegram")

async def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/fix_onboarding.py diagnose <telegram_id>")
        print("  python scripts/fix_onboarding.py reset <telegram_id>")
        print()
        print("Example:")
        print("  python scripts/fix_onboarding.py diagnose 8230716061")
        print("  python scripts/fix_onboarding.py reset 8230716061")
        return
    
    command = sys.argv[1]
    telegram_id = int(sys.argv[2]) if len(sys.argv) > 2 else 8230716061
    
    if command == "reset":
        await reset_onboarding(telegram_id)
    elif command == "diagnose":
        await diagnose_onboarding(telegram_id)
    else:
        print(f"Unknown command: {command}")
        print("Use 'diagnose' or 'reset'")

if __name__ == "__main__":
    asyncio.run(main())

