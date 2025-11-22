"""
Callback query handlers for inline keyboard buttons.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.models import User, PillarType
from sqlalchemy import select
from telegram_bot.conversation import ConversationState, get_conversation_state, get_conversation_context

logger = logging.getLogger(__name__)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboard buttons."""
    query = update.callback_query
    
    # Acknowledge the callback query to stop loading spinner
    await query.answer()
    
    user = update.effective_user
    callback_data = query.data
    
    logger.info(f"Received callback query: {callback_data} from user {user.id}")
    
    # Check conversation state
    from telegram_bot.conversation import get_conversation_state, ConversationState
    state = get_conversation_state(user.id)
    
    is_onboarding = state in [
        ConversationState.ONBOARDING,
        ConversationState.ONBOARDING_PILLARS,
        ConversationState.ONBOARDING_CUSTOM_PILLAR,
        ConversationState.ONBOARDING_WORK_HOURS,
        ConversationState.ONBOARDING_TIMEZONE,
        ConversationState.ONBOARDING_INITIAL_TASKS,
        ConversationState.ONBOARDING_HABITS,
        ConversationState.ONBOARDING_MOOD_TRACKING,
    ]
    
    is_task_creation = state in [
        ConversationState.ADDING_TASK,
        ConversationState.ADDING_TASK_PILLAR,
        ConversationState.ADDING_TASK_PRIORITY,
        ConversationState.ADDING_TASK_DUE_DATE,
        ConversationState.ADDING_TASK_DURATION,
    ]
    
    # Route onboarding callbacks to onboarding handler
    if (is_onboarding or 
        callback_data.startswith("onboarding_") or 
        callback_data.startswith("pillar_toggle_") or
        callback_data.startswith("timezone_")):
        from telegram_bot.handlers.onboarding_callbacks import handle_onboarding_callbacks
        await handle_onboarding_callbacks(update, context)
        return
    
    # Route natural language task creation callbacks
    if callback_data.startswith("nl_task_"):
        from telegram_bot.handlers.natural_language_tasks import handle_nl_task_callbacks
        await handle_nl_task_callbacks(update, context)
        return
    
    # Route insights callbacks (adaptive learning)
    if (callback_data.startswith("enable_flow_") or 
        callback_data == "insights_view" or 
        callback_data == "dismiss_pattern" or
        callback_data.startswith("create_recurring_task_") or
        callback_data.startswith("remind_later_")):
        from telegram_bot.handlers.insights_handler import handle_insights_callbacks
        await handle_insights_callbacks(update, context)
        return
    
    # Route task management callbacks (including pillar/priority during task creation)
    if (callback_data.startswith("task_") or 
        callback_data.startswith("filter_") or 
        callback_data.startswith("sort_") or
        is_task_creation and (callback_data.startswith("pillar_") or callback_data.startswith("priority_")) or
        (callback_data in ["confirm", "cancel"] and (not is_onboarding or is_task_creation))):
        from telegram_bot.handlers.task_callbacks import handle_task_callbacks
        await handle_task_callbacks(update, context)
        return
    
    # Route callback based on data prefix for non-onboarding, non-task-creation
    if callback_data.startswith("pillar_"):
        await handle_pillar_selection(update, context)
    elif callback_data == "yes" or callback_data == "no":
        await handle_yes_no_callback(update, context)
    elif callback_data.startswith("task_"):
        await handle_task_callback(update, context)
    elif callback_data.startswith("priority_"):
        await handle_priority_callback(update, context)
    elif callback_data == "confirm" or callback_data == "cancel":
        await handle_confirmation_callback(update, context)
    else:
        await query.message.reply_text(f"Unknown callback: {callback_data}")


async def handle_pillar_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pillar selection during onboarding."""
    query = update.callback_query
    user = update.effective_user
    callback_data = query.data
    
    # Extract pillar from callback data (format: "pillar_work")
    pillar_name = callback_data.replace("pillar_", "")
    
    logger.info(f"User {user.id} selected pillar: {pillar_name}")
    
    async with AsyncSessionLocal() as session:
        # Get user
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await query.message.reply_text("Please start with /start first.")
            return
        
        # Get conversation context
        conv_context = get_conversation_context(user.id)
        
        # Store selected pillars in context
        if "pillars" not in conv_context.data:
            conv_context.data["pillars"] = []
        
        if pillar_name not in conv_context.data["pillars"]:
            conv_context.data["pillars"].append(pillar_name)
            await query.answer(f"Added: {pillar_name.capitalize()} ✅")
        else:
            conv_context.data["pillars"].remove(pillar_name)
            await query.answer(f"Removed: {pillar_name.capitalize()} ❌")
        
        # Show current selection
        selected = conv_context.data.get("pillars", [])
        if selected:
            selected_text = ", ".join([p.capitalize() for p in selected])
            await query.message.edit_text(
                f"✅ Selected categories: {selected_text}\n\n"
                "You can select more categories or continue.\n\n"
                "When you're done selecting categories, type 'done' or send /start again to continue.",
                reply_markup=None  # Remove keyboard after selection
            )
        else:
            await query.message.edit_text(
                "No categories selected yet. Select at least one category to continue.",
                reply_markup=None
            )


async def handle_yes_no_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle yes/no callbacks."""
    query = update.callback_query
    await query.answer(f"You selected: {query.data.capitalize()}")
    await query.message.edit_text(f"Got it! You selected: {query.data.capitalize()}")


async def handle_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle task-related callbacks (complete, edit, delete, schedule)."""
    query = update.callback_query
    callback_data = query.data
    
    # Format: "task_complete_123" or "task_edit_123"
    parts = callback_data.split("_")
    if len(parts) >= 3:
        action = parts[1]  # complete, edit, delete, schedule
        task_id = int(parts[2])
        
        await query.answer(f"Task {action} action triggered for task {task_id}")
        await query.message.edit_text(f"Task {action} functionality coming soon!")


async def handle_priority_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle priority selection callbacks."""
    query = update.callback_query
    priority = query.data.replace("priority_", "")
    await query.answer(f"Priority set to: {priority.capitalize()}")
    await query.message.edit_text(f"✅ Priority set to: {priority.capitalize()}")


async def handle_confirmation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle confirmation/cancel callbacks."""
    query = update.callback_query
    action = query.data  # "confirm" or "cancel"
    
    if action == "confirm":
        await query.answer("Confirmed! ✅")
        await query.message.edit_text("✅ Confirmed!")
    else:
        await query.answer("Cancelled! ❌")
        await query.message.edit_text("❌ Cancelled.")

