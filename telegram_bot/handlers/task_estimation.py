"""
Task estimation confirmation handlers.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import Task, User
from sqlalchemy import select
from tasks.time_based_reminders import confirm_estimated_time
from clarifications.queue import add_clarification

logger = logging.getLogger(__name__)


async def ask_estimated_time(
    session: AsyncSession,
    user_id: int,
    task_id: int,
    application
) -> None:
    """
    Ask user to confirm estimated time for a task.
    
    Args:
        session: Database session
        user_id: User ID
        task_id: Task ID
        application: Telegram bot application
    """
    task = await session.get(Task, task_id)
    user = await session.get(User, user_id)
    
    if not task or not user:
        return
    
    # Check if already has estimated time
    if task.estimated_duration:
        # Ask for confirmation
        message = (
            f"⏱ **Task: {task.title}**\n\n"
            f"Current estimated time: {task.estimated_duration} minutes\n\n"
            f"Is this still accurate? Reply with:\n"
            f"• 'Yes' to keep it\n"
            f"• A number (e.g., '60') to update it\n"
            f"• 'Skip' to skip for now"
        )
    else:
        # Ask for initial estimate
        message = (
            f"⏱ **Task: {task.title}**\n\n"
            f"How long do you estimate this task will take?\n\n"
            f"Please reply with the number of minutes (e.g., '30', '60', '120').\n"
            f"This helps me remind you when to start working on it!"
        )
        
        # Add to clarification queue if not answered
        await add_clarification(
            session,
            user_id,
            f"How long will '{task.title}' take? (in minutes)",
            context={"task_id": task_id, "type": "estimated_time"},
            related_task_id=task_id,
            priority=2
        )
    
    try:
        await application.bot.send_message(
            chat_id=user.telegram_id,
            text=message,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error asking for estimated time: {e}")


async def handle_estimated_time_response(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    task_id: int,
    estimated_minutes: int
) -> None:
    """Handle user's response about estimated time."""
    user = update.effective_user
    
    async with AsyncSessionLocal() as session:
        # Get user
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            return
        
        # Confirm and update
        success = await confirm_estimated_time(session, db_user.id, task_id, estimated_minutes)
        
        if success:
            await update.message.reply_text(
                f"✅ Updated! I'll remind you when it's time to start this task.\n\n"
                f"Estimated: {estimated_minutes} minutes"
            )
            
            # Calculate and mention reminder time
            task = await session.get(Task, task_id)
            if task and task.due_date:
                from tasks.time_based_reminders import calculate_reminder_time
                reminder_time = await calculate_reminder_time(task)
                if reminder_time:
                    reminder_str = reminder_time.strftime('%Y-%m-%d %H:%M')
                    await update.message.reply_text(
                        f"📅 I'll remind you around {reminder_str} to start this task."
                    )
        else:
            await update.message.reply_text("❌ Error updating estimated time. Please try again.")

