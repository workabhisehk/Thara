"""
Task prioritization handlers.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from tasks.ai_prioritization import apply_ai_prioritization

logger = logging.getLogger(__name__)


async def prioritize_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /prioritize command - AI-driven task prioritization."""
    user = update.effective_user
    
    async with AsyncSessionLocal() as session:
        # Get user
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await update.message.reply_text("Please start with /start first.")
            return
        
        await update.message.reply_text(
            "🤖 Analyzing your tasks with AI...\n\n"
            "Considering:\n"
            "• Deadline urgency\n"
            "• Estimated duration\n"
            "• Task dependencies\n"
            "• Your work patterns\n"
            "• Workload balance"
        )
        
        # Get AI prioritization suggestions
        suggestions = await apply_ai_prioritization(session, db_user.id, auto_apply=False)
        
        if not suggestions:
            await update.message.reply_text("No tasks to prioritize.")
            return
        
        # Format suggestions
        message = "🎯 **AI Prioritization Suggestions:**\n\n"
        
        for i, item in enumerate(suggestions[:10], 1):
            task = item["task"]
            score = item["priority_score"]
            recommended = item["recommended_priority"]
            reasoning = item["reasoning"]
            
            current_emoji = "✅" if task.priority.value == recommended else "🔄"
            
            message += f"{i}. {current_emoji} **{task.title}**\n"
            message += f"   Current: {task.priority.value} → Recommended: {recommended}\n"
            message += f"   Score: {score}/100\n"
            message += f"   💡 {reasoning}\n\n"
        
        # Add apply button
        keyboard = [
            [InlineKeyboardButton("✅ Apply All Suggestions", callback_data="apply_prioritization")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_prioritization")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

