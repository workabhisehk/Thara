"""
Initialize database script.
"""
import asyncio
from database.connection import init_db, close_db

async def main():
    """Initialize database."""
    await init_db()
    await close_db()
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(main())

