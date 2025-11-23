"""
Database connection and session management.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError, DisconnectionError
from config import settings
import logging
import sys
import os
import asyncio
from typing import Optional, Callable, TypeVar, Awaitable, AsyncContextManager
from functools import wraps
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')

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
            pool_pre_ping=True,  # Verify connections before using
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_timeout=30,  # Timeout for getting connection from pool
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


async def reconnect_db():
    """
    Force reconnect to database by disposing and recreating the engine.
    Useful when schema changes occur or connection issues persist.
    """
    global engine, AsyncSessionLocal
    
    if engine is not None:
        logger.info("Disposing existing database engine...")
        await engine.dispose()
        engine = None
        AsyncSessionLocal = None
    
    logger.info("Reinitializing database engine...")
    _init_engines()
    logger.info("Database engine reconnected successfully")


async def check_connection_health() -> bool:
    """
    Check if database connection is healthy.
    Returns True if connection works, False otherwise.
    """
    if engine is None:
        try:
            _init_engines()
        except Exception as e:
            logger.error(f"Failed to initialize engine for health check: {e}")
            return False
    
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return False


async def retry_db_operation(
    operation: Callable[[AsyncSession], Awaitable[T]],
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0
) -> T:
    """
    Execute a database operation with retry logic.
    
    Args:
        operation: Async function that takes an AsyncSession and returns a result
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay between retries
    
    Returns:
        Result of the operation
    
    Raises:
        Exception: If all retries fail
    """
    if engine is None:
        _init_engines()
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            async with AsyncSessionLocal() as session:
                result = await operation(session)
                await session.commit()
                return result
        except (OperationalError, DisconnectionError, ConnectionError) as e:
            last_exception = e
            if attempt < max_retries:
                delay = initial_delay * (backoff_factor ** attempt)
                logger.warning(
                    f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
                
                # Try to reconnect
                try:
                    if engine is not None:
                        await engine.dispose()
                    _init_engines()
                except Exception as reconnect_error:
                    logger.warning(f"Failed to reconnect: {reconnect_error}")
            else:
                logger.error(f"Database operation failed after {max_retries + 1} attempts: {e}")
        except Exception as e:
            # For non-connection errors, don't retry
            logger.error(f"Database operation error (non-retryable): {e}")
            raise
    
    # If we get here, all retries failed
    raise ConnectionError(
        f"Database operation failed after {max_retries + 1} attempts. "
        f"Last error: {last_exception}"
    ) from last_exception


def with_db_session(
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0
):
    """
    Decorator for database operations with automatic retry logic.
    
    Usage:
        @with_db_session()
        async def my_handler(update, context):
            async with AsyncSessionLocal() as session:
                # Your database operations here
                pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # If function already uses AsyncSessionLocal, wrap it with retry logic
            # Otherwise, just call it normally
            try:
                return await func(*args, **kwargs)
            except (OperationalError, DisconnectionError, ConnectionError) as e:
                logger.warning(f"Database error in {func.__name__}: {e}. Retrying...")
                
                # Retry the entire function
                last_exception = e
                for attempt in range(max_retries):
                    try:
                        delay = initial_delay * (backoff_factor ** attempt)
                        await asyncio.sleep(delay)
                        
                        # Try to reconnect
                        try:
                            if engine is not None:
                                await engine.dispose()
                            _init_engines()
                        except Exception as reconnect_error:
                            logger.warning(f"Failed to reconnect: {reconnect_error}")
                        
                        return await func(*args, **kwargs)
                    except (OperationalError, DisconnectionError, ConnectionError) as retry_error:
                        last_exception = retry_error
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} failed: {retry_error}"
                        )
                
                # All retries failed
                raise ConnectionError(
                    f"Database operation in {func.__name__} failed after {max_retries + 1} attempts. "
                    f"Last error: {last_exception}"
                ) from last_exception
        
        return wrapper
    return decorator


@asynccontextmanager
async def get_db_session_with_retry(
    max_retries: int = 3,
    initial_delay: float = 0.5
) -> AsyncContextManager[AsyncSession]:
    """
    Get a database session with automatic retry on connection errors.
    
    This is a context manager that automatically retries on connection failures.
    
    Usage:
        async with get_db_session_with_retry() as session:
            # Your database operations here
            result = await session.execute(select(User))
            await session.commit()
    """
    if engine is None:
        _init_engines()
    
    last_exception = None
    session = None
    
    for attempt in range(max_retries + 1):
        try:
            session = AsyncSessionLocal()
            # Test the connection
            await session.execute(text("SELECT 1"))
            break  # Success, exit retry loop
        except (OperationalError, DisconnectionError, ConnectionError) as e:
            last_exception = e
            if session:
                try:
                    await session.close()
                except Exception:
                    pass
                session = None
            
            if attempt < max_retries:
                delay = initial_delay * (2.0 ** attempt)
                logger.warning(
                    f"Failed to get database session (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
                
                # Try to reconnect
                try:
                    if engine is not None:
                        await engine.dispose()
                    _init_engines()
                except Exception as reconnect_error:
                    logger.warning(f"Failed to reconnect: {reconnect_error}")
            else:
                logger.error(f"Failed to get database session after {max_retries + 1} attempts: {e}")
    
    # If we get here and session is None, all retries failed
    if session is None:
        raise ConnectionError(
            f"Failed to get database session after {max_retries + 1} attempts. "
            f"Last error: {last_exception}"
        ) from last_exception
    
    # Yield the session
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

