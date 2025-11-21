"""
Alternative database connection methods using Supabase client and REST API.
This provides a fallback when direct PostgreSQL connection fails.
"""
import os
import sys
from typing import Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Fix calendar module naming conflict
# The project's calendar/ directory shadows Python's built-in calendar module
# Import supabase before importing config to avoid the conflict
def _import_supabase_safely():
    """Import Supabase client, handling calendar module conflict."""
    try:
        # Temporarily rename calendar in sys.modules if needed
        import sys as sys_module
        if 'calendar' in sys_module.modules and hasattr(sys_module.modules['calendar'], '__file__'):
            calendar_path = sys_module.modules['calendar'].__file__
            if 'Thara' in str(calendar_path) and 'calendar' in str(calendar_path):
                # This is our local calendar module, temporarily remove it
                temp_calendar = sys_module.modules.pop('calendar', None)
                try:
                    from supabase import create_client
                    try:
                        from supabase.client import Client
                    except ImportError:
                        Client = None
                    return create_client, Client, True
                finally:
                    # Restore calendar module
                    if temp_calendar:
                        sys_module.modules['calendar'] = temp_calendar
                    else:
                        # Reload standard library calendar
                        import importlib
                        importlib.import_module('calendar')
        
        # Normal import path
        from supabase import create_client
        try:
            from supabase.client import Client
        except ImportError:
            Client = None
        return create_client, Client, True
    except ImportError:
        return None, None, False
    except Exception:
        # If there's any other error, try without calendar fix
        try:
            from supabase import create_client
            try:
                from supabase.client import Client
            except ImportError:
                Client = None
            return create_client, Client, True
        except Exception:
            return None, None, False

# Try to import Supabase client
_create_client, Client, SUPABASE_AVAILABLE = _import_supabase_safely()

if SUPABASE_AVAILABLE:
    create_client = _create_client
else:
    create_client = None

from config import settings

# Global Supabase client instance
_supabase_client: Optional['Client'] = None


def get_supabase_client() -> Optional['Client']:
    """
    Get Supabase client instance for REST API access.
    This works even if direct PostgreSQL connection fails.
    """
    global _supabase_client
    
    if not SUPABASE_AVAILABLE or not create_client:
        logger.error("Supabase client not available. Install with: pip install supabase")
        return None
    
    if _supabase_client is None:
        supabase_url = settings.supabase_url
        supabase_key = settings.supabase_key
        
        # Check if credentials are set
        if not supabase_url or supabase_url == "https://your-project.supabase.co":
            logger.warning("SUPABASE_URL not configured. Cannot use REST API connection.")
            return None
        
        if not supabase_key or supabase_key == "your_supabase_anon_key":
            logger.warning("SUPABASE_KEY not configured. Cannot use REST API connection.")
            return None
        
        try:
            _supabase_client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}")
            return None
    
    return _supabase_client


def test_supabase_connection() -> bool:
    """
    Test Supabase REST API connection.
    Returns True if connection works, False otherwise.
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Try a simple query to test connection
        # This will work even if direct PostgreSQL connection fails
        result = client.table('users').select('count', count='exact').limit(1).execute()
        logger.info("Supabase REST API connection successful")
        return True
    except Exception as e:
        logger.error(f"Supabase REST API connection failed: {e}")
        # Connection might still work, just table might not exist yet
        # This is okay for testing
        if "relation" in str(e).lower() or "does not exist" in str(e).lower():
            logger.info("Supabase client works, but tables don't exist yet (this is okay)")
            return True
        return False


class SupabaseDatabaseAdapter:
    """
    Adapter class to use Supabase REST API as database backend.
    This allows database operations without direct PostgreSQL connection.
    """
    
    def __init__(self):
        self.client = get_supabase_client()
        if not self.client:
            raise RuntimeError("Supabase client not available")
    
    def select(self, table: str, columns: str = "*", filters: Optional[dict] = None):
        """Select data from a table."""
        query = self.client.table(table).select(columns)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        return query.execute()
    
    def insert(self, table: str, data: dict):
        """Insert data into a table."""
        return self.client.table(table).insert(data).execute()
    
    def update(self, table: str, filters: dict, data: dict):
        """Update data in a table."""
        query = self.client.table(table)
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        return query.update(data).execute()
    
    def delete(self, table: str, filters: dict):
        """Delete data from a table."""
        query = self.client.table(table)
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        return query.delete().execute()


def check_connection_options() -> dict:
    """
    Check all available connection options and their status.
    Returns a dict with connection method statuses.
    """
    options = {
        "direct_postgresql": False,
        "supabase_rest_api": False,
        "connection_pooling": False,
    }
    
    # Check direct PostgreSQL connection
    try:
        import psycopg2
        from urllib.parse import urlparse
        import socket
        
        parsed = urlparse(settings.database_url)
        try:
            socket.gethostbyname(parsed.hostname)
            options["direct_postgresql"] = True
        except socket.gaierror:
            pass
    except Exception:
        pass
    
    # Check Supabase REST API
    if SUPABASE_AVAILABLE and get_supabase_client():
        options["supabase_rest_api"] = True
    
    # Check connection pooling (different hostname format)
    try:
        parsed = urlparse(settings.database_url)
        if "pooler.supabase.com" in parsed.hostname:
            options["connection_pooling"] = True
    except Exception:
        pass
    
    return options

