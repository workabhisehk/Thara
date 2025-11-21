#!/usr/bin/env python3
"""
Validate environment variables and configuration on startup.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from typing import List, Tuple

def validate_environment() -> Tuple[bool, List[str]]:
    """
    Validate all required environment variables.
    Returns (is_valid, list_of_errors)
    """
    errors = []
    warnings = []
    
    # Required settings
    required_settings = {
        'telegram_bot_token': 'TELEGRAM_BOT_TOKEN',
        'openai_api_key': 'OPENAI_API_KEY',
        'database_url': 'DATABASE_URL',
        'google_client_id': 'GOOGLE_CLIENT_ID',
        'google_client_secret': 'GOOGLE_CLIENT_SECRET',
        'google_redirect_uri': 'GOOGLE_REDIRECT_URI',
    }
    
    # Check required settings
    for attr, env_var in required_settings.items():
        try:
            value = getattr(settings, attr)
            if not value or value == f'your_{env_var.lower()}':
                errors.append(f"❌ {env_var} is not set or is a placeholder")
            elif len(str(value)) < 5:
                warnings.append(f"⚠️  {env_var} seems too short (might be invalid)")
        except Exception as e:
            errors.append(f"❌ {env_var} validation failed: {e}")
    
    # Optional but recommended settings
    optional_settings = {
        'gemini_api_key': 'GEMINI_API_KEY (optional fallback)',
    }
    
    for attr, name in optional_settings.items():
        try:
            value = getattr(settings, attr, None)
            if not value:
                warnings.append(f"ℹ️  {name} not set (optional but recommended)")
        except Exception:
            pass
    
    # Validate database URL format
    if settings.database_url:
        if not settings.database_url.startswith('postgresql://'):
            errors.append("❌ DATABASE_URL must start with 'postgresql://'")
        elif '@' not in settings.database_url:
            errors.append("❌ DATABASE_URL format seems invalid (missing @)")
    
    # Validate Telegram bot token format
    if settings.telegram_bot_token:
        if ':' not in settings.telegram_bot_token:
            warnings.append("⚠️  TELEGRAM_BOT_TOKEN format seems invalid (should be 'bot_id:token')")
    
    # Validate OpenAI API key format
    if settings.openai_api_key:
        if not settings.openai_api_key.startswith('sk-'):
            warnings.append("⚠️  OPENAI_API_KEY format seems invalid (should start with 'sk-')")
    
    # Validate Google OAuth redirect URI
    if settings.google_redirect_uri:
        if not (settings.google_redirect_uri.startswith('http://') or 
                settings.google_redirect_uri.startswith('https://')):
            warnings.append("⚠️  GOOGLE_REDIRECT_URI should start with 'http://' or 'https://'")
    
    is_valid = len(errors) == 0
    
    return is_valid, errors, warnings

def main():
    """Main validation function."""
    print("🔍 Validating Environment Configuration")
    print("=" * 60)
    print()
    
    is_valid, errors, warnings = validate_environment()
    
    if errors:
        print("❌ ERRORS FOUND:")
        print("-" * 60)
        for error in errors:
            print(f"  {error}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        print("-" * 60)
        for warning in warnings:
            print(f"  {warning}")
        print()
    
    if is_valid:
        print("✅ All required environment variables are set!")
        print()
        print("📋 Configuration Summary:")
        print("-" * 60)
        print(f"  ✅ Telegram Bot Token: {'*' * 20}...")
        print(f"  ✅ OpenAI API Key: {'*' * 20}...")
        print(f"  ✅ Database URL: {settings.database_url[:50]}...")
        print(f"  ✅ Google Client ID: {settings.google_client_id[:30]}...")
        print(f"  ✅ Google Redirect URI: {settings.google_redirect_uri}")
        
        if hasattr(settings, 'gemini_api_key') and settings.gemini_api_key:
            print(f"  ✅ Gemini API Key: {'*' * 20}... (optional)")
        else:
            print(f"  ℹ️  Gemini API Key: Not set (optional)")
        
        print()
        print("🎉 Environment validation passed!")
        return True
    else:
        print("❌ Environment validation failed!")
        print()
        print("📋 Next steps:")
        print("  1. Check your .env file")
        print("  2. Ensure all required variables are set")
        print("  3. Remove placeholder values")
        print("  4. Run this validation again")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

