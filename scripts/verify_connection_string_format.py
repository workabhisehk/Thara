#!/usr/bin/env python3
"""
Verify connection string format and show correct format.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from urllib.parse import urlparse

print("🔍 Verifying Connection String Format")
print("=" * 60)

url = settings.database_url
parsed = urlparse(url)

print(f"\nCurrent Connection String:")
print(f"{url[:80]}...")
print()

print("Parsed Components:")
print(f"  Username: {parsed.username}")
print(f"  Password: {'*' * len(parsed.password) if parsed.password else '❌ None (MISSING!)'}")
print(f"  Hostname: {parsed.hostname}")
print(f"  Port: {parsed.port}")
print(f"  Database: {parsed.path[1:] if parsed.path else 'None'}")
print()

# Extract project reference
project_ref = None
if parsed.hostname and parsed.hostname.startswith("db."):
    project_ref = parsed.hostname.replace("db.", "").replace(".supabase.co", "")

issues = []

if not parsed.password:
    issues.append("❌ PASSWORD IS MISSING from connection string!")
    print("⚠️  ISSUE FOUND: Password is missing!")
    print()
    print("Your connection string should have format:")
    print("postgresql://postgres.PROJECT_REF:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres")
    print()
    print("Current format appears to be:")
    print(f"postgresql://{parsed.username}@db... (missing password!)")
    print()
    print("💡 SOLUTION:")
    print("1. Go to Supabase Dashboard → Settings → Database")
    print("2. Copy the ENTIRE connection string from 'URI' tab")
    print("3. Make sure it includes the password after the colon")
    print("   Format: postgresql://postgres.PROJECT_REF:YOUR_PASSWORD@db...")
    print()
    
if parsed.username and project_ref and not parsed.username.startswith(f"postgres.{project_ref}"):
    issues.append("❌ Username format might be wrong")
    print("⚠️  Username format check:")
    if project_ref:
        expected = f"postgres.{project_ref}"
        print(f"   Current: {parsed.username}")
        print(f"   Expected: {expected}")
        if parsed.username != expected:
            print(f"   Should be: {expected}")
    print()

if issues:
    print("=" * 60)
    print("❌ ISSUES FOUND:")
    for issue in issues:
        print(f"   {issue}")
    print()
    print("📋 To fix:")
    print("1. Open your .env file")
    print("2. Find the DATABASE_URL line")
    print("3. Get the correct connection string from Supabase Dashboard")
    print("4. Replace the entire DATABASE_URL value")
    print("5. Make sure the format is:")
    print("   DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres")
    print("   (with NO spaces, NO quotes around the URL)")
else:
    print("✅ Connection string format looks correct!")

print()

