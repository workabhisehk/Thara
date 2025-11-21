#!/usr/bin/env python3
"""
Validate and test DATABASE_URL format.
"""
import os
import sys
from urllib.parse import urlparse, quote
from sqlalchemy.engine.url import make_url

# Load .env if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

db_url = os.getenv("DATABASE_URL", "")

# If not in env, try reading from .env file directly
if not db_url:
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    db_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

if not db_url:
    print("❌ DATABASE_URL not found in environment or .env file")
    print("Please set DATABASE_URL in your .env file")
    sys.exit(1)

# Remove any leading "DATABASE_URL=" if present
if db_url.startswith("DATABASE_URL="):
    db_url = db_url.split("=", 1)[1].strip().strip('"').strip("'")

print(f"Original URL: {db_url[:60]}...")

# Try to parse with SQLAlchemy
try:
    parsed = make_url(db_url)
    print("✅ URL format is valid!")
    print(f"   Database: {parsed.database}")
    print(f"   Host: {parsed.host}")
    print(f"   Port: {parsed.port}")
    print(f"   Username: {parsed.username}")
    print(f"   Password: {'*' * len(parsed.password) if parsed.password else 'None'}")
except Exception as e:
    print(f"❌ URL parsing failed: {e}")
    print("\nTroubleshooting:")
    
    # Check if password has special characters
    parsed_manual = urlparse(db_url)
    if parsed_manual.password:
        # Check for special characters
        special_chars = ['[', ']', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '+', '=', '{', '}', '|', '\\', ':', ';', '"', "'", '<', '>', ',', '.', '?', '/']
        found_special = [c for c in parsed_manual.password if c in special_chars]
        
        if found_special:
            print(f"   ⚠️  Password contains special characters: {found_special}")
            print(f"   📝 Original password: {parsed_manual.password}")
            encoded_password = quote(parsed_manual.password, safe='')
            print(f"   ✅ URL-encoded password: {encoded_password}")
            
            # Reconstruct URL
            netloc = f"{parsed_manual.username}:{encoded_password}@{parsed_manual.hostname}"
            if parsed_manual.port:
                netloc += f":{parsed_manual.port}"
            
            fixed_url = f"{parsed_manual.scheme}://{netloc}{parsed_manual.path}"
            if parsed_manual.query:
                fixed_url += f"?{parsed_manual.query}"
            
            print(f"\n   🔧 Fixed URL:")
            print(f"   {fixed_url}")
            print(f"\n   Copy this to your .env file as DATABASE_URL")
        else:
            print("   Check your DATABASE_URL format")
            print("   Expected: postgresql://user:password@host:port/database")
    sys.exit(1)

