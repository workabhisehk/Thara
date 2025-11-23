#!/usr/bin/env python3
"""
Check calendar connection status for a user.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from google_calendar.auth import get_authorization_url

async def check_calendar_connection(telegram_id: int):
    """Check calendar connection status and provide OAuth link if needed."""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            print(f"❌ User with telegram_id {telegram_id} not found")
            print("   Run /start in Telegram first to create the user")
            return
        
        print("=" * 60)
        print("Calendar Connection Status")
        print("=" * 60)
        print(f"User: {db_user.first_name} (ID: {db_user.id})")
        print(f"Telegram ID: {db_user.telegram_id}")
        print(f"Calendar Connected: {db_user.google_calendar_connected}")
        print()
        
        if db_user.google_calendar_connected:
            print("✅ Google Calendar is connected!")
            print(f"   Access Token: {'Set' if db_user.google_access_token else 'Missing'}")
            print(f"   Refresh Token: {'Set' if db_user.google_refresh_token else 'Missing'}")
            print(f"   Token Expires: {db_user.google_token_expires_at}")
        else:
            print("⚠️  Google Calendar is NOT connected")
            print()
            print("To connect:")
            print("  1. Use /calendar command in Telegram")
            print("  2. Or use this authorization URL:")
            print()
            try:
                auth_url = get_authorization_url(db_user.id)
                print(f"  {auth_url}")
                print()
                print("  3. After authorizing, complete the OAuth callback")
            except Exception as e:
                print(f"  ❌ Error generating auth URL: {e}")
                print("     Check your GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")

if __name__ == "__main__":
    telegram_id = int(sys.argv[1]) if len(sys.argv) > 1 else 8230716061
    asyncio.run(check_calendar_connection(telegram_id))

