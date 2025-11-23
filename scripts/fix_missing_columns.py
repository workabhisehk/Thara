#!/usr/bin/env python3
"""
Fix missing database columns by checking and adding them if needed.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import sync_engine, _init_engines
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_add_columns():
    """Check if columns exist and add them if missing."""
    _init_engines()
    
    if sync_engine is None:
        logger.error("Sync engine not initialized")
        return False
    
    with sync_engine.connect() as conn:
        # Check if preferred_name column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'preferred_name'
        """))
        has_preferred_name = result.fetchone() is not None
        
        # Check if conversation_state column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'conversation_state'
        """))
        has_conversation_state = result.fetchone() is not None
        
        # Check if conversation_context column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'conversation_context'
        """))
        has_conversation_context = result.fetchone() is not None
        
        logger.info(f"Column status:")
        logger.info(f"  preferred_name: {'✓' if has_preferred_name else '✗'}")
        logger.info(f"  conversation_state: {'✓' if has_conversation_state else '✗'}")
        logger.info(f"  conversation_context: {'✓' if has_conversation_context else '✗'}")
        
        # Add missing columns
        if not has_preferred_name:
            logger.info("Adding preferred_name column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN preferred_name VARCHAR"))
            conn.commit()
            logger.info("✓ Added preferred_name column")
        
        if not has_conversation_state:
            logger.info("Adding conversation_state column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN conversation_state VARCHAR DEFAULT 'idle'"))
            conn.commit()
            logger.info("✓ Added conversation_state column")
        
        if not has_conversation_context:
            logger.info("Adding conversation_context column...")
            # For PostgreSQL, use JSONB type
            conn.execute(text("ALTER TABLE users ADD COLUMN conversation_context JSONB"))
            conn.commit()
            logger.info("✓ Added conversation_context column")
        
        if has_preferred_name and has_conversation_state and has_conversation_context:
            logger.info("✓ All columns exist!")
            return True
        
        return True

if __name__ == "__main__":
    try:
        check_and_add_columns()
        logger.info("✓ Database columns fixed!")
    except Exception as e:
        logger.error(f"❌ Error fixing columns: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

