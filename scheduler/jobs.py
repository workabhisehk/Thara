"""
APScheduler job definitions.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import pytz
from config import settings
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def sync_calendar_for_all_users():
    """Sync calendar for all connected users."""
    from google_calendar.sync import sync_calendar
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(
            User.google_calendar_connected == True,
            User.is_active == True
        )
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        for user in users:
            try:
                await sync_calendar(session, user.id)
            except Exception as e:
                logger.error(f"Error syncing calendar for user {user.id}: {e}")

scheduler = AsyncIOScheduler(timezone=pytz.UTC)


async def init_scheduler():
    """Initialize and start scheduler."""
    # Add jobs
    from scheduler import daily_kickoff, checkins, weekly_review, reminders
    
    # Daily kickoff - runs at work start hour (default 8am) for each user
    # This is a placeholder - actual implementation will schedule per-user
    scheduler.add_job(
        daily_kickoff.send_daily_summaries,
        trigger=CronTrigger(hour=settings.default_work_start_hour, minute=0),
        id='daily_kickoff',
        replace_existing=True
    )
    
    # 30-minute check-ins - runs every 30 minutes during work hours
    scheduler.add_job(
        checkins.send_check_ins,
        trigger=IntervalTrigger(minutes=settings.check_in_interval),
        id='check_ins',
        replace_existing=True
    )
    
    # Weekly review - Sunday at 10am
    scheduler.add_job(
        weekly_review.send_weekly_review,
        trigger=CronTrigger(day_of_week='sun', hour=settings.weekly_review_hour, minute=0),
        id='weekly_review',
        replace_existing=True
    )
    
    # Deadline reminders - every hour
    scheduler.add_job(
        reminders.send_deadline_reminders,
        trigger=IntervalTrigger(hours=1),
        id='deadline_reminders',
        replace_existing=True
    )
    
    # Deadline escalation - every 6 hours
    scheduler.add_job(
        reminders.escalate_deadlines,
        trigger=IntervalTrigger(hours=6),
        id='deadline_escalation',
        replace_existing=True
    )
    
    # Calendar sync - every 4 hours
    from google_calendar.sync import sync_calendar
    scheduler.add_job(
        sync_calendar_for_all_users,
        trigger=IntervalTrigger(hours=4),
        id='calendar_sync',
        replace_existing=True
    )
    
    # Time-based reminders - every 30 minutes
    from scheduler.time_reminders import check_time_based_reminders
    scheduler.add_job(
        check_time_based_reminders,
        trigger=IntervalTrigger(minutes=30),
        id='time_based_reminders',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started")


async def shutdown_scheduler():
    """Shutdown scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped")

