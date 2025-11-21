"""
Supabase client initialization that handles calendar module conflict.
Import this instead of directly importing from supabase to avoid conflicts.
"""
import sys
import importlib

def get_supabase_imports():
    """
    Safely import Supabase client, handling calendar module naming conflict.
    Returns (create_client, Client) or (None, None) if import fails.
    """
    try:
        # Save and temporarily remove local calendar module if present
        local_calendar = None
        if 'calendar' in sys.modules:
            cal_mod = sys.modules['calendar']
            if hasattr(cal_mod, '__file__') and cal_mod.__file__:
                file_path = str(cal_mod.__file__)
                if '/Thara/calendar' in file_path or 'Thara\\calendar' in file_path:
                    local_calendar = sys.modules.pop('calendar')
        
        try:
            # Now import supabase (uses standard library calendar)
            from supabase import create_client
            try:
                from supabase.client import Client
            except ImportError:
                Client = None
            
            return create_client, Client
        finally:
            # Restore local calendar module if we removed it
            if local_calendar:
                # Get standard library calendar first
                import calendar as stdlib_cal
                # Store it for httpx to use
                if 'calendar_stdlib' not in sys.modules:
                    sys.modules['calendar_stdlib'] = stdlib_cal
                # Restore local calendar
                sys.modules['calendar'] = local_calendar
    
    except ImportError:
        return None, None
    except Exception:
        return None, None

# Import at module level
create_client, Client = get_supabase_imports()

__all__ = ['create_client', 'Client', 'get_supabase_imports']

