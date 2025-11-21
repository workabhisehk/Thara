#!/usr/bin/env python3
"""
Test different connection string formats to diagnose the issue.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
import psycopg2
from urllib.parse import urlparse, quote
import socket

def test_dns(hostname):
    """Test DNS resolution for a hostname."""
    try:
        ip = socket.gethostbyname(hostname)
        return True, ip
    except socket.gaierror as e:
        return False, str(e)

def test_connection_url(url, description):
    """Test a connection URL."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"URL: {url[:70]}...")
    print(f"{'='*60}")
    
    try:
        parsed = urlparse(url)
        print(f"Parsed components:")
        print(f"  Hostname: {parsed.hostname}")
        print(f"  Port: {parsed.port}")
        print(f"  Username: {parsed.username}")
        print(f"  Database: {parsed.path[1:] if parsed.path else 'N/A'}")
        
        # Test DNS
        print(f"\nDNS resolution test...")
        can_resolve, result = test_dns(parsed.hostname)
        if can_resolve:
            print(f"✅ DNS resolves to: {result}")
        else:
            print(f"❌ DNS resolution failed: {result}")
            return False
        
        # Try connection
        print(f"\nConnection test...")
        conn = psycopg2.connect(url)
        print(f"✅ Connection successful!")
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Database version: {version[:60]}...")
        cursor.close()
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Test different connection string formats."""
    print("🔍 Connection String Diagnostic Tool")
    print("=" * 60)
    
    # Get current connection string
    current_url = settings.database_url
    print(f"\nCurrent DATABASE_URL from .env:")
    print(f"{current_url[:70]}...")
    
    parsed = urlparse(current_url)
    print(f"\nParsed hostname: {parsed.hostname}")
    
    # Test current URL
    success = test_connection_url(current_url, "Current Connection String")
    
    if not success:
        print("\n" + "="*60)
        print("⚠️  Current connection string failed!")
        print("="*60)
        
        # Check if it's a pooler URL issue
        if "pooler.supabase.com" not in parsed.hostname:
            print("\n💡 Suggestion: Try using Connection Pooling URL")
            print("   1. Go to Supabase Dashboard → Settings → Database")
            print("   2. Scroll to 'Connection pooling' section")
            print("   3. Select 'Transaction' mode")
            print("   4. Copy the pooler connection string")
            print("   5. Update your .env file with it")
            print("\n   Pooler URLs use:")
            print("   - Hostname: aws-0-REGION.pooler.supabase.com")
            print("   - Port: 6543 (instead of 5432)")
        
        # Check hostname format
        if not parsed.hostname.startswith("db."):
            print("\n💡 Suggestion: Verify hostname format")
            print("   Should be: db.PROJECT_REF.supabase.co")
            print(f"   Current: {parsed.hostname}")
        
        # Check username format
        if parsed.username and not parsed.username.startswith("postgres."):
            print("\n💡 Suggestion: Verify username format")
            print("   Should be: postgres.PROJECT_REF")
            print(f"   Current: {parsed.username}")
    
    print("\n" + "="*60)
    print("✅ Diagnostic complete!")
    print("="*60)

if __name__ == "__main__":
    main()

