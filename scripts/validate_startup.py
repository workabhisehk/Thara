#!/usr/bin/env python3
"""
Validate that all required components are set up correctly before starting the bot.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_config():
    """Validate all required configuration is present."""
    errors = []
    warnings = []
    
    print("🔍 Validating Configuration...")
    print("=" * 60)
    
    # Required settings
    required_settings = {
        "telegram_bot_token": "TELEGRAM_BOT_TOKEN",
        "openai_api_key": "OPENAI_API_KEY",
        "database_url": "DATABASE_URL",
        "google_client_id": "GOOGLE_CLIENT_ID",
        "google_client_secret": "GOOGLE_CLIENT_SECRET",
        "google_redirect_uri": "GOOGLE_REDIRECT_URI",
    }
    
    for attr, env_name in required_settings.items():
        try:
            value = getattr(settings, attr)
            if not value or value == f"your_{attr}":
                errors.append(f"❌ {env_name} is not set or invalid")
            else:
                masked = value[:10] + "..." if len(value) > 10 else value
                print(f"✅ {env_name}: {masked}")
        except Exception as e:
            errors.append(f"❌ {env_name}: {str(e)}")
    
    # Optional settings
    optional_settings = {
        "gemini_api_key": "GEMINI_API_KEY",
    }
    
    for attr, env_name in optional_settings.items():
        try:
            value = getattr(settings, attr, None)
            if value:
                print(f"✅ {env_name}: Set (optional)")
            else:
                warnings.append(f"⚠️  {env_name}: Not set (optional)")
        except Exception:
            pass
    
    # Test database connection
    print("\n🔍 Testing Database Connection...")
    try:
        import psycopg2
        from urllib.parse import urlparse
        parsed = urlparse(settings.database_url)
        
        conn = psycopg2.connect(settings.database_url, connect_timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Database connection: Successful")
        print(f"   Version: {version[:50]}...")
        
        # Check if tables exist
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name != 'alembic_version'
        """)
        table_count = cursor.fetchone()[0]
        print(f"✅ Tables created: {table_count} tables")
        
        # Check pgvector
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
        has_vector = cursor.fetchone()[0]
        if has_vector:
            print(f"✅ pgvector extension: Installed")
        else:
            warnings.append("⚠️  pgvector extension not installed")
        
        cursor.close()
        conn.close()
    except Exception as e:
        errors.append(f"❌ Database connection failed: {str(e)}")
    
    # Test Telegram bot token format
    print("\n🔍 Validating Telegram Bot Token...")
    try:
        token = settings.telegram_bot_token
        if ":" in token and len(token) > 20:
            print(f"✅ Telegram bot token: Valid format")
        else:
            errors.append("❌ Telegram bot token format invalid")
    except Exception as e:
        errors.append(f"❌ Telegram bot token validation failed: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   {warning}")
    
    if errors:
        print("\n❌ Errors (must fix before starting bot):")
        for error in errors:
            print(f"   {error}")
        print("\n💡 Fix the errors above before starting the bot.")
        return False
    else:
        print("\n✅ All required configuration is valid!")
        print("🚀 You can start the bot with: python bot_main.py")
        return True

if __name__ == "__main__":
    success = validate_config()
    sys.exit(0 if success else 1)

