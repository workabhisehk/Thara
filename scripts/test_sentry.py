#!/usr/bin/env python3
"""
Test script to verify Sentry is working correctly.
This will trigger a test error to Sentry.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

# Initialize Sentry
if settings.sentry_dsn and settings.sentry_enabled:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=1.0,
        integrations=[
            LoggingIntegration(
                level=10,  # DEBUG
                event_level=40  # ERROR
            ),
        ],
    )
    print("✅ Sentry initialized!")
else:
    print("⚠️ Sentry not configured. Set SENTRY_DSN in .env file")
    print("   Go to https://sentry.io to get your DSN")

# Test error capture
def test_error():
    """Test that Sentry captures errors."""
    try:
        # This will raise an error
        result = 1 / 0
    except Exception as e:
        if settings.sentry_dsn and settings.sentry_enabled:
            import sentry_sdk
            sentry_sdk.capture_exception(e)
            print("✅ Test error sent to Sentry!")
            print(f"   Error: {e}")
            print("\n   Check your Sentry dashboard to see the error")
        else:
            print("❌ Sentry not configured, cannot send error")

# Test with user context (like Telegram bot errors)
def test_error_with_user_context():
    """Test error with user context (simulates Telegram user)."""
    try:
        if settings.sentry_dsn and settings.sentry_enabled:
            import sentry_sdk
            
            # Simulate Telegram user context
            sentry_sdk.set_user({
                "id": 8230716061,  # Your Telegram ID
                "username": "test_user",
                "first_name": "Test",
            })
            
            # Simulate a database-like error
            raise ValueError("Test error: telegram_id value out of range")
            
    except Exception as e:
        if settings.sentry_dsn and settings.sentry_enabled:
            import sentry_sdk
            sentry_sdk.capture_exception(e)
            print("✅ Test error with user context sent to Sentry!")
            print(f"   Error: {e}")
            print("   User context: {id: 8230716061, username: test_user}")
            print("\n   Check your Sentry dashboard - you should see:")
            print("   - The error with full stack trace")
            print("   - User information (Telegram ID, username)")
        else:
            print("❌ Sentry not configured, cannot send error")

if __name__ == "__main__":
    print("=" * 60)
    print("Sentry Test Script")
    print("=" * 60)
    print()
    
    if not settings.sentry_dsn:
        print("⚠️ SENTRY_DSN not set in .env file")
        print()
        print("To set up Sentry:")
        print("1. Go to https://sentry.io and create an account")
        print("2. Create a new Python project")
        print("3. Copy your DSN")
        print("4. Add to .env file:")
        print("   SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx")
        print()
        sys.exit(1)
    
    print("Testing Sentry error capture...")
    print()
    
    # Test 1: Simple error
    print("Test 1: Simple error capture")
    test_error()
    print()
    
    # Test 2: Error with user context
    print("Test 2: Error with user context (Telegram-like)")
    test_error_with_user_context()
    print()
    
    print("=" * 60)
    print("✅ Tests completed!")
    print("=" * 60)
    print()
    print("Check your Sentry dashboard to verify errors were received:")
    print("https://sentry.io")
    print()
    print("Wait a few seconds for events to appear...")

