"""
Message handlers for manual task scheduling.
"""
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from telegram_bot.conversation import (
    ConversationState,
    get_conversation_state,
    get_conversation_context,
    set_conversation_state,
    clear_conversation_context,
)
from edge_cases.validation import validate_due_date

logger = logging.getLogger(__name__)


async def handle_scheduling_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle manual scheduling input message."""
    user = update.effective_user
    text = update.message.text.strip()
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await update.message.reply_text("Please start with /start first.")
            clear_conversation_context(user.id)
            return
        
        conv_context = get_conversation_context(user.id)
        task_id = conv_context.data.get("scheduling_task_id")
        
        if not task_id:
            await update.message.reply_text(
                "No task found for scheduling. Please start over by selecting a task."
            )
            clear_conversation_context(user.id)
            set_conversation_state(user.id, ConversationState.NORMAL)
            return
        
        # Parse the time input using validation helpers
        is_valid, error_msg, parsed_date = validate_due_date(text, allow_past=False)
        
        if not is_valid or not parsed_date:
            await update.message.reply_text(
                f"⚠️ {error_msg}\n\n"
                "Please try again with a valid time (e.g., 'tomorrow 2pm', 'Dec 25 10am', 'next Monday 9am'):"
            )
            return
        
        # Get task to calculate end time
        from tasks.service import get_task
        task = await get_task(session, task_id, db_user.id)
        
        if not task:
            await update.message.reply_text("Task not found.")
            clear_conversation_context(user.id)
            set_conversation_state(user.id, ConversationState.NORMAL)
            return
        
        # Calculate end time
        start_time = parsed_date
        if task.estimated_duration:
            from datetime import timedelta
            end_time = start_time + timedelta(minutes=task.estimated_duration)
        else:
            end_time = start_time + timedelta(hours=1)  # Default 1 hour
        
        # Schedule the task
        from tasks.scheduling import schedule_task_to_calendar
        
        success, event_id, error_msg = await schedule_task_to_calendar(
            session,
            db_user.id,
            task_id,
            start_time,
            end_time
        )
        
        if not success:
            await update.message.reply_text(
                f"⚠️ **Scheduling Failed**\n\n{error_msg}\n\n"
                "Please try again with a different time.",
                parse_mode="Markdown"
            )
            return
        
        await session.commit()
        
        # Clear scheduling context
        clear_conversation_context(user.id)
        set_conversation_state(user.id, ConversationState.NORMAL)
        
        time_str = start_time.strftime('%Y-%m-%d %I:%M %p')
        await update.message.reply_text(
            f"✅ **Task Scheduled!**\n\n"
            f"**Task:** {task.title}\n\n"
            f"**Time:** {time_str}\n\n"
            "The task has been added to your Google Calendar.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📋 View Tasks", callback_data="task_menu")
            ]])
        )
        
        logger.info(f"Task {task_id} manually scheduled to calendar at {time_str}")

