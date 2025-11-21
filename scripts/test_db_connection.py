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
    print(f"Database URL format: {settings.database_url[:60]}...")
    
    try:
        # Parse URL
        parsed = urlparse(settings.database_url)
        print(f"\nParsed components:")
        print(f"  Host: {parsed.hostname}")
        print(f"  Port: {parsed.port}")
        print(f"  Database: {parsed.path[1:] if parsed.path else 'N/A'}")
        print(f"  User: {parsed.username}")
        print(f"  Password: {'*' * len(parsed.password) if parsed.password else 'None'}")
        
        # Test DNS resolution first
        import socket
        print(f"\n🔍 Testing DNS resolution...")
        try:
            ip = socket.gethostbyname(parsed.hostname)
            print(f"✅ Hostname resolves to: {ip}")
        except socket.gaierror as e:
            print(f"❌ DNS resolution failed: {e}")
            print("\n⚠️  Your Supabase project appears to be PAUSED!")
            print("   Free tier projects pause after ~7 days of inactivity.")
            print("\n📋 To fix:")
            print("   1. Go to https://supabase.com/dashboard")
            print("   2. Find your paused project")
            print("   3. Click 'Restore' or 'Resume'")
            print("   4. Wait 1-2 minutes for it to wake up")
            print("   5. Run this test again")
            return False
        
        # Try to connect
        print("\n🔌 Attempting database connection...")
        conn = psycopg2.connect(settings.database_url)
        print("✅ Connection successful!")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Database version: {version[:50]}...")
        cursor.close()
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        if "could not translate host name" in str(e):
            print("\n⚠️  DNS/Hostname resolution issue!")
            print("   Your Supabase project might be paused.")
            print("\n📋 To fix:")
            print("   1. Check https://supabase.com/dashboard")
            print("   2. Restore your paused project if needed")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your DATABASE_URL in .env file")
        print("2. Verify Supabase project is active (not paused)")
        print("3. Check network connectivity")
        print("4. Ensure DATABASE_URL format is: postgresql://user:password@host:port/database")
        print("5. Verify your password is URL-encoded if it has special characters")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

