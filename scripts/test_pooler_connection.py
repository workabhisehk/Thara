#!/usr/bin/env python3
"""
Test connection with pooler URL if direct connection fails.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
import psycopg2
from urllib.parse import urlparse
import socket

def test_dns(hostname):
    """Test DNS resolution."""
    try:
        ip = socket.gethostbyname(hostname)
        return True, ip
    except socket.gaierror as e:
        return False, str(e)

def main():
    """Test current connection string."""
    print("🔍 Testing Connection String")
    print("=" * 60)
    
    url = settings.database_url
    parsed = urlparse(url)
    
    print(f"Current connection string:")
    print(f"  {url[:80]}...")
    print()
    print(f"Components:")
    print(f"  Username: {parsed.username}")
    print(f"  Hostname: {parsed.hostname}")
    print(f"  Port: {parsed.port}")
    print()
    
    # Check if it's a pooler URL
    is_pooler = "pooler.supabase.com" in parsed.hostname
    if is_pooler:
        print("✅ Using Connection Pooling URL (pooler.supabase.com)")
    else:
        print("ℹ️  Using Direct Connection URL (db.*.supabase.co)")
        print()
        print("💡 If DNS fails, try Connection Pooling instead:")
        print("   1. Go to Supabase Dashboard → Settings → Database")
        print("   2. Scroll to 'Connection pooling' section")
        print("   3. Select 'Transaction' mode")
        print("   4. Copy the pooler connection string")
        print("   5. Update .env file with it")
    
    print()
    print("Testing DNS resolution...")
    can_resolve, result = test_dns(parsed.hostname)
    
    if can_resolve:
        print(f"✅ DNS resolves to: {result}")
        print()
        print("Testing connection...")
        try:
            conn = psycopg2.connect(url)
            print("✅ Connection successful!")
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Database version: {version[:60]}...")
            cursor.close()
            conn.close()
            print()
            print("🎉 SUCCESS! Your database connection is working!")
            return True
        except psycopg2.OperationalError as e:
            print(f"❌ Connection failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    else:
        print(f"❌ DNS resolution failed: {result}")
        print()
        if not is_pooler:
            print("⚠️  Direct connection DNS failed.")
            print("   This could mean:")
            print("   - Project is still waking up (wait 2-3 minutes)")
            print("   - DNS hasn't propagated yet")
            print("   - Network/firewall blocking")
            print()
            print("💡 Try Connection Pooling URL instead (often more reliable)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

