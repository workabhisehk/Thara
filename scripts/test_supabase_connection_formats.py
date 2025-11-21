#!/usr/bin/env python3
"""
Test different Supabase connection string formats.
Based on Supabase documentation: https://github.com/orgs/supabase/discussions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from urllib.parse import urlparse
import psycopg2
import socket

def extract_project_ref(hostname):
    """Extract project reference from hostname."""
    # Try to extract project ref from various formats
    if hostname.startswith("db."):
        return hostname.replace("db.", "").replace(".supabase.co", "")
    elif ".supabase.co" in hostname:
        return hostname.replace(".supabase.co", "")
    return None

def test_connection(connection_string, description):
    """Test a connection string."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"{'='*60}")
    parsed = urlparse(connection_string)
    print(f"Hostname: {parsed.hostname}")
    print(f"Port: {parsed.port}")
    
    # Test DNS first
    try:
        ip = socket.gethostbyname(parsed.hostname)
        print(f"✅ DNS resolves to: {ip}")
    except socket.gaierror as e:
        print(f"❌ DNS resolution failed: {e}")
        return False
    
    # Test connection
    try:
        conn = psycopg2.connect(connection_string, connect_timeout=10)
        print("✅ Connection successful!")
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
    """Test various connection string formats."""
    print("🔍 Testing Supabase Connection String Formats")
    print("Based on Supabase documentation")
    print("="*60)
    
    current_url = settings.database_url
    parsed = urlparse(current_url)
    
    print(f"\nCurrent connection string:")
    print(f"  {current_url[:80]}...")
    print(f"\nExtracted components:")
    print(f"  Username: {parsed.username}")
    print(f"  Hostname: {parsed.hostname}")
    print(f"  Port: {parsed.port}")
    print(f"  Database: {parsed.path[1:] if parsed.path else 'postgres'}")
    
    # Extract project reference
    project_ref = extract_project_ref(parsed.hostname)
    if not project_ref:
        print("\n❌ Could not extract project reference from hostname")
        return
    
    print(f"\n  Project Reference: {project_ref}")
    
    # Build connection strings to test
    username = parsed.username
    password = parsed.password
    database = parsed.path[1:] if parsed.path else "postgres"
    
    connection_variants = [
        # Direct connection (standard format without db. prefix)
        (
            f"postgresql://{username}:{password}@{project_ref}.supabase.co:5432/{database}",
            f"Direct connection (standard format: {project_ref}.supabase.co:5432)"
        ),
        # Direct connection with db. prefix (current)
        (
            f"postgresql://{username}:{password}@db.{project_ref}.supabase.co:5432/{database}",
            f"Direct connection with db. prefix (current: db.{project_ref}.supabase.co:5432)"
        ),
        # Connection pooler - Transaction mode
        (
            f"postgresql://{username}:{password}@{project_ref}.supabase.co:6543/{database}",
            f"Connection pooler - Transaction mode (port 6543)"
        ),
        # Connection pooler - Session mode (if available)
        (
            f"postgresql://{username}:{password}@{project_ref}.supabase.co:5432/{database}?pgbouncer=true",
            f"Connection pooler - Session mode (port 5432 with pgbouncer)"
        ),
    ]
    
    # Test each variant
    success_count = 0
    for conn_string, description in connection_variants:
        if test_connection(conn_string, description):
            success_count += 1
            print(f"\n🎉 SUCCESS! Working connection string found!")
            print(f"\nWorking connection string:")
            print(f"  {conn_string}")
            print(f"\n📝 Update your .env file with:")
            print(f"  DATABASE_URL={conn_string}")
            break
    
    if success_count == 0:
        print(f"\n{'='*60}")
        print("❌ All connection formats failed")
        print("="*60)
        print("\n💡 Troubleshooting steps:")
        print("  1. Verify project reference is correct")
        print("  2. Check Supabase dashboard → Settings → Database")
        print("  3. Get fresh connection string from dashboard")
        print("  4. Ensure password is correctly URL-encoded")
        print("  5. Check if project needs to be restored")
        print("  6. Try using connection pooler URL from dashboard")

if __name__ == "__main__":
    main()

