#!/usr/bin/env python3
"""
Fix connection string format - shows what's wrong and generates correct format.
"""
import sys
import os
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

print("🔍 Connection String Analysis")
print("=" * 60)

current_url = settings.database_url
parsed = urlparse(current_url)

print(f"\nCurrent Connection String:")
print(f"  {current_url[:80]}...")

print(f"\nParsed Components:")
print(f"  Username: {parsed.username}")
print(f"  Password: {'*' * len(parsed.password) if parsed.password else 'None'}")
print(f"  Hostname: {parsed.hostname}")
print(f"  Port: {parsed.port}")
print(f"  Database: {parsed.path[1:] if parsed.path else 'None'}")

# Extract project reference from hostname
project_ref = None
if parsed.hostname:
    if parsed.hostname.startswith("db.") and parsed.hostname.endswith(".supabase.co"):
        project_ref = parsed.hostname.replace("db.", "").replace(".supabase.co", "")
        print(f"\n✅ Project Reference extracted: {project_ref}")
    elif "pooler.supabase.com" in parsed.hostname:
        # For pooler URLs, extract from username
        if parsed.username and "." in parsed.username:
            project_ref = parsed.username.split(".", 1)[1]
            print(f"\n✅ Project Reference extracted from username: {project_ref}")

# Check username format
issues = []
if parsed.username:
    if not parsed.username.startswith("postgres."):
        issues.append("❌ Username format is WRONG!")
        print(f"\n⚠️  ISSUE FOUND:")
        print(f"   Current username: {parsed.username}")
        if project_ref:
            correct_username = f"postgres.{project_ref}"
            print(f"   Should be: {correct_username}")
            
            # Generate correct connection string
            print(f"\n📝 CORRECT CONNECTION STRING FORMAT:")
            print(f"   {parsed.scheme}://{correct_username}:{parsed.password}@{parsed.hostname}:{parsed.port}{parsed.path}")
            print(f"\n   Copy this to your .env file as DATABASE_URL")
        else:
            print(f"   Should be: postgres.PROJECT_REF")
            print(f"   (Replace PROJECT_REF with your actual project reference)")
    else:
        print(f"\n✅ Username format is correct!")
else:
    issues.append("❌ Username is missing!")

# Check hostname
if parsed.hostname:
    if not parsed.hostname.endswith(".supabase.co") and "pooler.supabase.com" not in parsed.hostname:
        issues.append("❌ Hostname format might be wrong!")
        print(f"\n⚠️  Hostname doesn't look like Supabase format")
        print(f"   Current: {parsed.hostname}")
        print(f"   Should end with: .supabase.co or contain: pooler.supabase.com")

print("\n" + "=" * 60)

if issues:
    print("⚠️  ISSUES FOUND:")
    for issue in issues:
        print(f"   {issue}")
    print("\n📋 HOW TO FIX:")
    print("   1. Go to Supabase Dashboard → Settings → Database")
    print("   2. Click 'URI' tab under 'Connection string'")
    print("   3. Copy the ENTIRE connection string shown there")
    print("   4. Replace DATABASE_URL in your .env file with it")
    print("\n   The correct format will have:")
    print("   - Username: postgres.PROJECT_REF (not just 'postgres')")
    print("   - Hostname: db.PROJECT_REF.supabase.co")
else:
    print("✅ Connection string format looks correct!")
    print("   If connection still fails, check:")
    print("   - DNS resolution (project might be paused)")
    print("   - Password is correct")
    print("   - Network/firewall settings")

print("=" * 60)

