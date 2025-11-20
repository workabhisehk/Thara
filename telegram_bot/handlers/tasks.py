"""
Task management handlers.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tasks command."""
    user = update.effective_user
    
    async with AsyncSessionLocal() as session:
        # Get user's tasks
        from database.models import Task, User
        from sqlalchemy import select
        
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await update.message.reply_text("Please start with /start first.")
            return
        
        # Get tasks
        tasks_stmt = select(Task).where(
            Task.user_id == db_user.id,
            Task.status.in_(["pending", "in_progress"])
        ).order_by(
            Task.priority.desc(),
            Task.due_date.asc()
        ).limit(10)
        
        tasks_result = await session.execute(tasks_stmt)
        tasks = tasks_result.scalars().all()
        
        if not tasks:
            await update.message.reply_text(
                "You don't have any active tasks. Add one by saying:\n"
                '"Add task: [your task description]"'
            )
            return
        
        # Format tasks list
        tasks_text = "📋 **Your Active Tasks:**\n\n"
        for i, task in enumerate(tasks, 1):
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority.value, "⚪")
            due_str = f" (due: {task.due_date.strftime('%Y-%m-%d')})" if task.due_date else ""
            tasks_text += f"{i}. {priority_emoji} {task.title}{due_str}\n"
        
        await update.message.reply_text(tasks_text, parse_mode="Markdown")

