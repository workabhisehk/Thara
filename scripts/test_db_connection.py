#!/usr/bin/env python3
"""
Test database connection script.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
import psycopg2
from urllib.parse import urlparse

def test_connection():
    """Test database connection."""
    print("Testing database connection...")
    print(f"Database URL format: {settings.database_url[:50]}...")
    
    try:
        # Parse URL
        parsed = urlparse(settings.database_url)
        print(f"\nParsed components:")
        print(f"  Host: {parsed.hostname}")
        print(f"  Port: {parsed.port}")
        print(f"  Database: {parsed.path[1:] if parsed.path else 'N/A'}")
        print(f"  User: {parsed.username}")
        
        # Try to connect
        print("\nAttempting connection...")
        conn = psycopg2.connect(settings.database_url)
        print("✅ Connection successful!")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your DATABASE_URL in .env file")
        print("2. Verify Supabase project is active")
        print("3. Check network connectivity")
        print("4. Ensure DATABASE_URL format is: postgresql://user:password@host:port/database")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

