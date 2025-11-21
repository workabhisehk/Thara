"""
Alternative database connection methods using Supabase client and REST API.
This provides a fallback when direct PostgreSQL connection fails.
"""
import os
import sys
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Try to import Supabase client
try:
    from supabase import create_client
    try:
        from supabase.client import Client
    except ImportError:
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from supabase.client import Client
        else:
            Client = None
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None  # Type stub
    if not os.getenv("SUPABASE_URL"):
        # Only warn if we're trying to use it
        pass

from config import settings

# Global Supabase client instance
_supabase_client: Optional['Client'] = None


def get_supabase_client() -> Optional[Client]:
    """
    Get Supabase client instance for REST API access.
    This works even if direct PostgreSQL connection fails.
    """
    global _supabase_client
    
    if not SUPABASE_AVAILABLE:
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

