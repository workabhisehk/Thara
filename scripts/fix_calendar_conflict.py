#!/usr/bin/env python3
"""
Fix calendar module naming conflict by temporarily removing it from path.
"""
import sys
import os
from pathlib import Path

# Remove current directory from path to avoid calendar module conflict
project_root = Path(__file__).parent.parent
if str(project_root) in sys.path:
    sys.path.remove(str(project_root))

# Add project root back, but after site-packages
sys.path.insert(0, str(project_root / "venv" / "lib" / "python3.12" / "site-packages"))
sys.path.append(str(project_root))

# Now test Supabase import
try:
    from supabase import create_client
    print("✅ Supabase import works!")
    print("✅ Calendar conflict resolved")
    
    # Test actual connection
    sys.path.insert(0, str(project_root))
    from config import settings
    
    if settings.supabase_url and settings.supabase_url != "https://your-project.supabase.co":
        client = create_client(settings.supabase_url, settings.supabase_key)
        print("✅ Supabase client created successfully!")
    else:
        print("⚠️  Supabase credentials not configured yet")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

