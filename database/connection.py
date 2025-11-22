"""
Database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings
import logging
import sys
import os

logger = logging.getLogger(__name__)

# Create base class for models
Base = declarative_base()

# Lazy initialization to avoid creating engines during Alembic imports
engine = None
sync_engine = None
AsyncSessionLocal = None
SessionLocal = None

def _is_alembic_running():
    """Check if Alembic is running."""
    return "alembic" in sys.argv[0] or any("alembic" in arg for arg in sys.argv)

def _init_engines():
    """Initialize database engines. Called lazily to avoid issues during Alembic imports."""
    global engine, sync_engine, AsyncSessionLocal, SessionLocal
    
    if engine is None:
        # Create async engine
        # Convert postgresql:// to postgresql+asyncpg:// for async support
        async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Remove ALL query parameters (asyncpg doesn't support them in URL)
        # Extract SSL requirement and convert to proper SSL parameter for asyncpg
        from urllib.parse import urlparse, parse_qs, urlunparse
        parsed = urlparse(async_database_url)
        query_params = parse_qs(parsed.query)
        
        # Check if SSL is required before removing query params
        ssl_required = False
        if 'sslmode' in query_params:
            ssl_mode = query_params['sslmode'][0] if query_params['sslmode'] else 'require'
            # asyncpg requires SSL for secure connections
            ssl_required = ssl_mode in ('require', 'prefer', 'allow', 'verify-ca', 'verify-full')
        
        # Remove ALL query parameters - asyncpg doesn't support any query params
        # Reconstruct URL without any query parameters
        async_database_url = urlunparse(parsed._replace(query=''))
        
        # Set SSL parameter for asyncpg (True = enable SSL)
        connect_args = {}
        if ssl_required:
            # asyncpg uses ssl=True for SSL connections
            connect_args['ssl'] = True
        
        engine = create_async_engine(
            async_database_url,
            echo=settings.environment == "development",
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args=connect_args
        )

        # Create async session factory
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

    if sync_engine is None:
        # Create sync engine for Alembic migrations
        # psycopg2 supports sslmode, so we can use it directly
        sync_database_url = settings.database_url
        sync_engine = create_engine(
            sync_database_url,
            echo=settings.environment == "development",
            pool_pre_ping=True
        )

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Only initialize engines if not running Alembic
if not _is_alembic_running():
    try:
        _init_engines()
    except Exception as e:
        # If initialization fails (e.g., URL parsing error), log but don't crash
        # This allows Alembic to import the module and handle URL parsing itself
        logger.warning(f"Could not initialize engines during import: {e}")


async def get_db() -> AsyncSession:
    """
    Dependency for getting database session.
    Use in FastAPI route dependencies.
    """
    if engine is None:
        _init_engines()
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    if engine is None:
        _init_engines()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


async def close_db():
    """Close database connections."""
    if engine is not None:
        await engine.dispose()
    logger.info("Database connections closed")

