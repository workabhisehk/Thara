#!/usr/bin/env python3
"""
Test connection via Supabase REST API as alternative.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
import requests

def test_supabase_api():
    """Test if Supabase REST API is accessible."""
    print("=" * 60)
    print("Alternative: Testing Supabase REST API")
    print("=" * 60)
    print()
    print("If database connection fails, you can use Supabase REST API")
    print("to interact with your database as an alternative.")
    print()
    
    supabase_url = settings.supabase_url
    supabase_key = settings.supabase_key
    
    if not supabase_url or supabase_url == "https://your-project.supabase.co":
        print("⚠️  SUPABASE_URL not configured")
        print("   You can get this from Supabase Dashboard → Settings → API")
        print("   This is an alternative way to interact with your database")
        return False
    
    if not supabase_key or supabase_key == "your_supabase_anon_key":
        print("⚠️  SUPABASE_KEY not configured")
        print("   You can get this from Supabase Dashboard → Settings → API")
        return False
    
    print(f"Supabase URL: {supabase_url}")
    print(f"API Key configured: {'*' * 20}...")
    print()
    
    # Test API health
    try:
        response = requests.get(f"{supabase_url}/rest/v1/", headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}"
        }, timeout=10)
        
        if response.status_code == 200:
            print("✅ Supabase REST API is accessible!")
            print("   You can use this as an alternative to direct database connection")
            return True
        else:
            print(f"⚠️  API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    test_supabase_api()

