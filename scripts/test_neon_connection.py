#!/usr/bin/env python3
"""
Test Neon DB connection.
Neon uses standard PostgreSQL connection strings.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
import psycopg2
from urllib.parse import urlparse
import socket

def test_connection():
    """Test Neon DB connection."""
    print("🔍 Testing Neon DB Connection")
    print("=" * 60)
    print()
    
    url = settings.database_url
    print(f"Connection string: {url[:80]}...")
    
    try:
        # Parse URL
        parsed = urlparse(url)
        print(f"\nParsed components:")
        print(f"  Host: {parsed.hostname}")
        print(f"  Port: {parsed.port}")
        print(f"  Database: {parsed.path[1:] if parsed.path else 'postgres'}")
        print(f"  User: {parsed.username}")
        print(f"  Password: {'*' * len(parsed.password) if parsed.password else 'None'}")
        
        # Test DNS resolution
        print(f"\n🔍 Testing DNS resolution...")
        try:
            ip = socket.gethostbyname(parsed.hostname)
            print(f"✅ Hostname resolves to: {ip}")
        except socket.gaierror as e:
            print(f"❌ DNS resolution failed: {e}")
            print("\n⚠️  Check your Neon connection string")
            print("   Get it from: https://console.neon.tech")
            print("   Project → Connect → Connection String")
            return False
        
        # Try to connect
        print("\n🔌 Attempting database connection...")
        conn = psycopg2.connect(url, connect_timeout=10)
        print("✅ Connection successful!")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Database version: {version[:60]}...")
        
        # Check if pgvector extension is available
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
        has_vector = cursor.fetchone()[0]
        if has_vector:
            print("✅ pgvector extension is installed")
        else:
            print("⚠️  pgvector extension not found (will need to install)")
            print("   Run: CREATE EXTENSION IF NOT EXISTS vector;")
        
        cursor.close()
        conn.close()
        
        print()
        print("🎉 SUCCESS! Your Neon DB connection is working!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("  1. Check your DATABASE_URL in .env file")
        print("  2. Get connection string from Neon Console:")
        print("     https://console.neon.tech → Your Project → Connect")
        print("  3. Make sure password is URL-encoded if it has special characters")
        print("  4. Verify project is active (not paused)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Check your connection string format:")
        print("  Expected: postgresql://user:password@host:port/database")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

