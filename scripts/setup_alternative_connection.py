#!/usr/bin/env python3
"""
Setup and test alternative database connection methods.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from database.alternative_connection import (
    get_supabase_client,
    test_supabase_connection,
    check_connection_options
)

def main():
    """Setup and test alternative connection methods."""
    print("🔍 Setting Up Alternative Database Connections")
    print("=" * 60)
    print()
    
    # Check what connection options are available
    print("Checking available connection options...")
    options = check_connection_options()
    
    print("\nConnection Options Status:")
    print("-" * 60)
    print(f"  Direct PostgreSQL: {'✅ Available' if options['direct_postgresql'] else '❌ Not available (DNS failing)'}")
    print(f"  Supabase REST API: {'✅ Available' if options['supabase_rest_api'] else '❌ Not available'}")
    print(f"  Connection Pooling: {'✅ Available' if options['connection_pooling'] else '❌ Not configured'}")
    print()
    
    # Check if Supabase credentials are configured
    print("Checking Supabase credentials...")
    print("-" * 60)
    
    supabase_url = settings.supabase_url
    supabase_key = settings.supabase_key
    
    if not supabase_url or supabase_url == "https://your-project.supabase.co":
        print("❌ SUPABASE_URL not configured")
        print()
        print("📋 To set it up:")
        print("   1. Go to Supabase Dashboard → Settings → API")
        print("   2. Copy 'Project URL' (e.g., https://xvdfxjujaotozyjflxcb.supabase.co)")
        print("   3. Add to .env file as: SUPABASE_URL=https://xvdfxjujaotozyjflxcb.supabase.co")
    else:
        print(f"✅ SUPABASE_URL configured: {supabase_url}")
    
    if not supabase_key or supabase_key == "your_supabase_anon_key":
        print("❌ SUPABASE_KEY not configured")
        print()
        print("📋 To set it up:")
        print("   1. Go to Supabase Dashboard → Settings → API")
        print("   2. Copy 'anon public' key")
        print("   3. Add to .env file as: SUPABASE_KEY=your_key_here")
    else:
        print(f"✅ SUPABASE_KEY configured: {'*' * 20}...")
    
    print()
    
    # Test Supabase REST API connection if credentials are set
    if supabase_url and supabase_url != "https://your-project.supabase.co" and \
       supabase_key and supabase_key != "your_supabase_anon_key":
        print("Testing Supabase REST API connection...")
        print("-" * 60)
        
        try:
            if test_supabase_connection():
                print("✅ Supabase REST API connection successful!")
                print()
                print("🎉 You can use Supabase REST API as an alternative to direct PostgreSQL connection.")
                print("   This works even if direct connection fails.")
            else:
                print("⚠️  Supabase REST API connection failed or tables don't exist yet.")
                print("   This is okay if you haven't created tables yet.")
        except ImportError:
            print("❌ Supabase Python client not installed")
            print()
            print("📋 To install it:")
            print("   pip install supabase")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("⚠️  Cannot test Supabase REST API - credentials not configured")
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    if options['supabase_rest_api']:
        print("✅ Supabase REST API is available and can be used as an alternative connection method.")
    else:
        print("📋 Next steps:")
        if not options['direct_postgresql']:
            print("   1. Restore your Supabase project in the dashboard (it's likely paused)")
            print("   2. OR configure Supabase REST API credentials (see above)")
        
        if not options['supabase_rest_api']:
            print("   1. Install Supabase client: pip install supabase")
            print("   2. Add SUPABASE_URL and SUPABASE_KEY to your .env file")
            print("   3. Get credentials from Supabase Dashboard → Settings → API")

if __name__ == "__main__":
    main()

