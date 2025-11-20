"""
Start command and onboarding flow handler.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from telegram_bot.conversation import ConversationState, set_conversation_state, get_conversation_context, get_conversation_state
from telegram_bot.keyboards import get_pillar_keyboard, get_yes_no_keyboard

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    
    async with AsyncSessionLocal() as session:
        # Check if user exists
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if db_user and db_user.is_onboarded:
            # User already onboarded
            await update.message.reply_text(
                f"Welcome back, {user.first_name}! 👋\n\n"
                "I'm your productivity assistant. How can I help you today?\n\n"
                "Use /help to see available commands."
            )
        else:
            # New user or not onboarded
            if not db_user:
                # Create new user
                db_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                session.add(db_user)
                await session.commit()
                await session.refresh(db_user)
            
            # Start onboarding
            set_conversation_state(user.id, ConversationState.ONBOARDING)
            
            await update.message.reply_text(
                f"Hello {user.first_name}! 👋\n\n"
                "I'm your AI Productivity Agent. My mission is to help you manage tasks, "
                "schedule commitments, and maintain productivity across work, education, and personal domains.\n\n"
                "Let's get you set up! This will only take a few minutes.\n\n"
                "First, which categories (pillars) would you like to track?\n"
                "You can select multiple:"
            )
            
            await update.message.reply_text(
                "Select your categories:",
                reply_markup=get_pillar_keyboard()
            )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = """
📚 **Available Commands:**

/start - Start or restart the bot
/help - Show this help message
/settings - Manage your settings
/tasks - View and manage tasks
/calendar - Calendar operations

💬 **Natural Language:**
You can also just chat with me naturally! Try:
- "Add task: Prepare presentation for client meeting"
- "What's on my calendar today?"
- "Show me my tasks"
- "Schedule time for project review"

I'll understand and help you manage your productivity!
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle natural language messages."""
    user = update.effective_user
    text = update.message.text
    
    # Get conversation state
    state = get_conversation_state(user.id)
    context_data = get_conversation_context(user.id)
    
    # Store conversation
    from memory.conversation_store import store_conversation
    async with AsyncSessionLocal() as session:
        await store_conversation(
            session,
            user_id=user.id,
            message_id=update.message.message_id,
            text=text,
            is_from_user=True
        )
        await session.commit()
    
    # Route based on state
    if state == ConversationState.ONBOARDING:
        # Continue onboarding flow
        await handle_onboarding_message(update, context)
    else:
        # Process natural language with AI
        await handle_natural_language(update, context)


async def handle_onboarding_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages during onboarding."""
    # This will be expanded with full onboarding flow
    await update.message.reply_text(
        "I'm processing your onboarding. Please use the buttons provided or /start to restart."
    )


async def handle_natural_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle natural language with AI."""
    # This will use AI service to understand intent
    await update.message.reply_text(
        "I'm processing your message. AI integration coming soon!"
    )

