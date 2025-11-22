#!/usr/bin/env python3
"""
Debug script to troubleshoot database connection issues.
Tests the exact code path the bot uses.
"""
import sys
import os
import asyncio
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("🔍 Database Connection Troubleshooting")
print("=" * 60)
print()

# Step 1: Check config
print("Step 1: Checking configuration...")
try:
    from config import settings
    print(f"✅ Config loaded")
    print(f"   Database URL: {settings.database_url[:60]}...")
    
    from urllib.parse import urlparse
    parsed = urlparse(settings.database_url)
    print(f"   Host: {parsed.hostname}")
    print(f"   Port: {parsed.port}")
    print(f"   Database: {parsed.path[1:] if parsed.path else 'N/A'}")
    print(f"   Query params: {parsed.query}")
except Exception as e:
    print(f"❌ Config error: {e}")
    traceback.print_exc()
    sys.exit(1)

print()

# Step 2: Test connection string processing
print("Step 2: Testing connection string processing...")
try:
    from database.connection import _init_engines
    
    # Reset engines to force recreation
    from database import connection as db_conn
    db_conn.engine = None
    db_conn.AsyncSessionLocal = None
    
    print("   Initializing engines...")
    _init_engines()
    
    # Check the processed URL
    if db_conn.engine:
        url = str(db_conn.engine.url)
        print(f"✅ Engine created")
        print(f"   Processed URL: {url[:80]}...")
        
        # Check if query params were removed
        parsed_url = urlparse(url)
        if parsed_url.query:
            print(f"   ⚠️  Warning: URL still has query params: {parsed_url.query}")
        else:
            print(f"   ✅ Query params removed correctly")
except Exception as e:
    print(f"❌ Engine initialization error: {e}")
    traceback.print_exc()
    sys.exit(1)

print()

# Step 3: Test async session
print("Step 3: Testing async database session...")
try:
    from database.connection import AsyncSessionLocal
    from database.models import User
    from sqlalchemy import select
    
    async def test_session():
        try:
            async with AsyncSessionLocal() as session:
                print("   ✅ Session created successfully")
                
                # Try a simple query
                stmt = select(User).limit(1)
                result = await session.execute(stmt)
                users = result.scalars().all()
                print(f"   ✅ Query executed successfully (found {len(users)} users)")
                return True
        except Exception as e:
            print(f"   ❌ Session error: {e}")
            traceback.print_exc()
            return False
    
    success = asyncio.run(test_session())
    if not success:
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Async session error: {e}")
    traceback.print_exc()
    sys.exit(1)

print()

# Step 4: Test the exact code path used by /start command
print("Step 4: Testing /start command code path...")
try:
    from database.connection import AsyncSessionLocal
    from database.models import User
    from sqlalchemy import select
    
    async def test_start_command():
        try:
            # This is the exact code from start_command handler
            async with AsyncSessionLocal() as session:
                # Simulate user ID
                test_user_id = 12345
                
                stmt = select(User).where(User.telegram_id == test_user_id)
                print("   Executing query...")
                result = await session.execute(stmt)
                print("   ✅ Query executed")
                
                db_user = result.scalar_one_or_none()
                print(f"   ✅ Query completed (user exists: {db_user is not None})")
                return True
        except Exception as e:
            print(f"   ❌ Error in /start code path: {e}")
            traceback.print_exc()
            return False
    
    success = asyncio.run(test_start_command())
    if not success:
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Start command test error: {e}")
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("✅ All tests passed! Database connection is working.")
print("=" * 60)
print()
print("If the bot still shows errors:")
print("  1. Make sure bot is completely stopped (Ctrl+C)")
print("  2. Check if there are other running instances: ps aux | grep bot_main")
print("  3. Kill all instances: pkill -9 -f bot_main.py")
print("  4. Restart bot: python bot_main.py")
print()

