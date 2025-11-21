#!/usr/bin/env python3
"""
Debug .env file reading issues.
"""
import os
import sys
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"

print("🔍 Debugging .env File")
print("=" * 60)

# Check if .env exists
if not env_file.exists():
    print("❌ .env file not found!")
    print(f"   Expected location: {env_file}")
    sys.exit(1)

print(f"✅ .env file found at: {env_file}")
print()

# Read .env file directly
print("Reading .env file directly...")
print("-" * 60)
with open(env_file, 'r') as f:
    lines = f.readlines()

database_url_line = None
for i, line in enumerate(lines, 1):
    line = line.rstrip()
    if line.startswith("DATABASE_URL"):
        database_url_line = (i, line)
        # Show the line (mask password)
        if ":" in line and "@" in line:
            parts = line.split("@")
            if len(parts) > 0 and ":" in parts[0]:
                user_pass = parts[0].split(":")
                if len(user_pass) > 1:
                    masked = ":".join(user_pass[:-1]) + ":***MASKED***@" + "@".join(parts[1:])
                    print(f"Line {i}: {masked}")
                else:
                    print(f"Line {i}: {line[:50]}...")
            else:
                print(f"Line {i}: {line[:80]}...")
        else:
            print(f"Line {i}: {line[:80]}...")

if not database_url_line:
    print("❌ DATABASE_URL not found in .env file!")
    sys.exit(1)

print()

# Parse the line
line_num, full_line = database_url_line
print(f"Analyzing DATABASE_URL on line {line_num}...")
print("-" * 60)

# Extract value (handle different formats)
if "=" in full_line:
    value = full_line.split("=", 1)[1]
    # Remove quotes if present
    value = value.strip().strip('"').strip("'").strip()
    
    print(f"Raw value (first 80 chars): {value[:80]}...")
    print()
    
    # Check for common issues
    issues = []
    
    if value.startswith("DATABASE_URL"):
        issues.append("Value still contains 'DATABASE_URL=' prefix")
    
    if " " in value and not value.startswith("postgresql://"):
        issues.append("Contains spaces (might be trimmed)")
    
    if value.startswith('"') and value.endswith('"'):
        issues.append("Wrapped in double quotes (should be removed)")
    
    if value.startswith("'") and value.endswith("'"):
        issues.append("Wrapped in single quotes (should be removed)")
    
    # Check format
    if not value.startswith("postgresql://"):
        issues.append(f"Doesn't start with 'postgresql://' (starts with: {value[:20]})")
    
    # Parse username
    if "@" in value:
        user_pass_host = value.split("@", 1)[0]
        if ":" in user_pass_host:
            username = user_pass_host.rsplit(":", 1)[0]
            if not username.startswith("postgres."):
                issues.append(f"Username doesn't start with 'postgres.' (found: {username[:20]})")
    
    # Show issues
    if issues:
        print("⚠️  Potential Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ No obvious formatting issues detected")
    
    print()
    
    # Test loading with different methods
    print("Testing environment variable loading...")
    print("-" * 60)
    
    # Method 1: Set directly in environment
    os.environ["DATABASE_URL"] = value
    
    # Method 2: Test with pydantic-settings
    try:
        from pydantic_settings import BaseSettings
        from pydantic import Field
        
        class TestSettings(BaseSettings):
            database_url: str = Field(..., env="DATABASE_URL")
            
            class Config:
                env_file = ".env"
                env_file_encoding = "utf-8"
        
        test_settings = TestSettings()
        loaded_url = test_settings.database_url
        
        print(f"✅ Pydantic loaded: {loaded_url[:60]}...")
        
        # Compare
        if loaded_url != value:
            print(f"⚠️  Loaded value differs from .env file value!")
            print(f"   .env file:  {value[:60]}...")
            print(f"   Loaded:     {loaded_url[:60]}...")
            print(f"   Difference might be due to post-processing in config.py")
        else:
            print("✅ Values match")
            
        # Now test with actual config
        print()
        print("Testing with actual config.py...")
        print("-" * 60)
        sys.path.insert(0, str(project_root))
        from config import settings
        
        actual_url = settings.database_url
        print(f"✅ Config loaded: {actual_url[:60]}...")
        
        # Parse and check components
        from urllib.parse import urlparse
        parsed = urlparse(actual_url)
        
        print()
        print("Parsed components:")
        print(f"  Username: {parsed.username}")
        print(f"  Password: {'*' * len(parsed.password) if parsed.password else 'None'}")
        print(f"  Hostname: {parsed.hostname}")
        print(f"  Port: {parsed.port}")
        print(f"  Database: {parsed.path[1:] if parsed.path else 'None'}")
        
        # Verify username format
        if parsed.username and not parsed.username.startswith("postgres."):
            print()
            print("⚠️  USERNAME FORMAT ISSUE:")
            print(f"   Current: {parsed.username}")
            print(f"   Should be: postgres.PROJECT_REF")
            print(f"   Example: postgres.xvdfxjujaotozyjflxcb")
        
    except Exception as e:
        print(f"❌ Error loading: {e}")
        import traceback
        traceback.print_exc()

else:
    print("❌ No '=' found in DATABASE_URL line")
    print(f"   Line content: {full_line[:80]}...")

print()
print("=" * 60)
print("✅ Debug complete!")

