#!/usr/bin/env python3
"""
Test various alternative connection methods.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from urllib.parse import urlparse
import socket
import subprocess

def test_method_1_psql():
    """Test using psql command line tool."""
    print("=" * 60)
    print("Method 1: Testing with psql command line")
    print("=" * 60)
    
    url = settings.database_url
    parsed = urlparse(url)
    
    # Build psql connection string
    # Format: psql "postgresql://user:pass@host:port/db"
    
    try:
        # Test if psql is available
        result = subprocess.run(['which', 'psql'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ psql not found. Install PostgreSQL client tools.")
            return False
        
        print(f"✅ psql found at: {result.stdout.strip()}")
        print()
        print("Attempting connection with psql...")
        print(f"Hostname: {parsed.hostname}")
        print(f"Port: {parsed.port}")
        print(f"Database: {parsed.path[1:] if parsed.path else 'postgres'}")
        print()
        
        # Test connection
        psql_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}{parsed.path}"
        result = subprocess.run(
            ['psql', psql_url, '-c', 'SELECT version();'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Connection successful with psql!")
            print(result.stdout)
            return True
        else:
            print(f"❌ Connection failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Connection timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_method_2_resolve_ip():
    """Try to resolve IP and connect directly."""
    print()
    print("=" * 60)
    print("Method 2: Resolving IP address")
    print("=" * 60)
    
    url = settings.database_url
    parsed = urlparse(url)
    
    print(f"Hostname: {parsed.hostname}")
    print()
    print("Testing DNS resolution methods...")
    
    # Try multiple DNS servers
    dns_methods = [
        ("gethostbyname", lambda h: socket.gethostbyname(h)),
        ("getaddrinfo", lambda h: socket.getaddrinfo(h, None)[0][4][0]),
    ]
    
    ip_address = None
    for method_name, method in dns_methods:
        try:
            ip = method(parsed.hostname)
            print(f"✅ {method_name}: {ip}")
            ip_address = ip
            break
        except Exception as e:
            print(f"❌ {method_name}: {e}")
    
    if ip_address:
        print()
        print(f"✅ Resolved IP: {ip_address}")
        print("You can try connecting using the IP address directly.")
        print("Note: IP-based connection might work even if DNS doesn't.")
        return ip_address
    else:
        print()
        print("❌ Could not resolve IP address")
        return None

def test_method_3_different_hostnames():
    """Try variations of hostname format."""
    print()
    print("=" * 60)
    print("Method 3: Testing different hostname formats")
    print("=" * 60)
    
    url = settings.database_url
    parsed = urlparse(url)
    
    # Extract project ref
    project_ref = None
    if parsed.hostname and parsed.hostname.startswith("db."):
        project_ref = parsed.hostname.replace("db.", "").replace(".supabase.co", "")
    
    if not project_ref:
        print("Could not extract project reference")
        return False
    
    print(f"Project Reference: {project_ref}")
    print()
    
    # Try different hostname formats
    hostname_variants = [
        f"db.{project_ref}.supabase.co",
        f"{project_ref}.supabase.co",
        f"db-{project_ref}.supabase.co",
        f"postgres.{project_ref}.supabase.co",
    ]
    
    print("Testing hostname variants...")
    for hostname in hostname_variants:
        try:
            ip = socket.gethostbyname(hostname)
            print(f"✅ {hostname} → {ip}")
        except socket.gaierror as e:
            print(f"❌ {hostname} → DNS failed")
    
    return False

def test_method_4_env_vars():
    """Test if environment variables are set correctly."""
    print()
    print("=" * 60)
    print("Method 4: Checking environment variables")
    print("=" * 60)
    
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print(f"✅ DATABASE_URL found in environment: {db_url[:60]}...")
    else:
        print("❌ DATABASE_URL not in environment variables")
        print("   Make sure you're loading .env file correctly")
    
    # Check if we can load from .env directly
    from pathlib import Path
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print(f"✅ .env file exists: {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith("DATABASE_URL"):
                    print(f"   Found DATABASE_URL in .env file")
                    break
    else:
        print(f"❌ .env file not found: {env_file}")
    
    return False

def test_method_5_asyncpg():
    """Try asyncpg library instead of psycopg2."""
    print()
    print("=" * 60)
    print("Method 5: Testing with asyncpg (async driver)")
    print("=" * 60)
    
    try:
        import asyncio
        import asyncpg
        
        url = settings.database_url
        parsed = urlparse(url)
        
        async def test_connection():
            try:
                conn = await asyncpg.connect(
                    host=parsed.hostname,
                    port=parsed.port or 5432,
                    user=parsed.username,
                    password=parsed.password,
                    database=parsed.path[1:] if parsed.path else 'postgres',
                    timeout=10
                )
                
                version = await conn.fetchval('SELECT version();')
                print(f"✅ Connection successful with asyncpg!")
                print(f"   Database version: {version[:60]}...")
                await conn.close()
                return True
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                return False
        
        result = asyncio.run(test_connection())
        return result
        
    except ImportError:
        print("❌ asyncpg not installed. Install with: pip install asyncpg")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all alternative connection tests."""
    print("🔍 Testing Alternative Connection Methods")
    print("=" * 60)
    print()
    
    methods = [
        ("Environment Variables", test_method_4_env_vars),
        ("IP Resolution", test_method_2_resolve_ip),
        ("Hostname Variants", test_method_3_different_hostnames),
        ("psql Command Line", test_method_1_psql),
        ("asyncpg Library", test_method_5_asyncpg),
    ]
    
    results = []
    for name, method in methods:
        try:
            result = method()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print("💡 If all methods fail, the issue is likely:")
    print("   - Supabase project is paused (restore it in dashboard)")
    print("   - Network/firewall blocking connections")
    print("   - Connection string format is still incorrect")
    print("   - Credentials are wrong")

if __name__ == "__main__":
    main()

