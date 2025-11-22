"""
Callback handlers for onboarding flow according to COMPREHENSIVE_PLAN.md
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from telegram_bot.conversation import (
    ConversationState, 
    get_conversation_state, 
    get_conversation_context, 
    set_conversation_state
)
from telegram_bot.handlers.onboarding import (
    get_enhanced_pillar_keyboard,
    get_timezone_keyboard,
    get_yes_no_maybe_keyboard,
    get_yes_no_tellme_keyboard,
    show_pillar_selection,
    store_pillars_and_continue,
    complete_onboarding,
    continue_to_habits,
)

logger = logging.getLogger(__name__)


async def handle_onboarding_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route onboarding-specific callbacks."""
    query = update.callback_query
    callback_data = query.data
    user = update.effective_user
    
    # Acknowledge callback immediately
    await query.answer()
    
    logger.info(f"Onboarding callback: {callback_data} from user {user.id}")
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await query.message.reply_text("Please start with /start first.")
            return
        
        # Route based on callback type
        if callback_data.startswith("pillar_toggle_"):
            await handle_pillar_toggle(update, context, session, db_user)
        elif callback_data == "onboarding_add_custom_pillar":
            await handle_add_custom_pillar_callback(update, context, session, db_user)
        elif callback_data == "onboarding_pillars_done":
            await handle_pillars_done(update, context, session, db_user)
        elif callback_data == "onboarding_pillars_skip":
            await handle_pillars_skip(update, context, session, db_user)
        elif callback_data.startswith("timezone_"):
            await handle_timezone_callback(update, context, session, db_user)
        elif callback_data in ["yes", "no", "maybe_later"]:
            await handle_onboarding_yes_no(update, context, session, db_user)
        elif callback_data == "tell_me_more":
            await handle_tell_me_more(update, context, session, db_user)
        else:
            await query.message.edit_text(f"Unknown callback: {callback_data}")


async def handle_pillar_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               session, db_user: User) -> None:
    """Handle pillar toggle (select/deselect) during onboarding."""
    query = update.callback_query
    callback_data = query.data
    user = update.effective_user
    
    # Extract pillar name (format: "pillar_toggle_work")
    pillar_name = callback_data.replace("pillar_toggle_", "")
    
    conv_context = get_conversation_context(user.id)
    
    # Initialize pillars list if needed
    if "pillars" not in conv_context.data:
        conv_context.data["pillars"] = []
    
    selected_pillars = conv_context.data["pillars"]
    custom_pillars = conv_context.data.get("custom_pillars", [])
    
    # Toggle pillar
    if pillar_name in selected_pillars:
        selected_pillars.remove(pillar_name)
        action = "Removed"
        emoji = "❌"
    else:
        selected_pillars.append(pillar_name)
        action = "Added"
        emoji = "✅"
    
    # Update keyboard with current selection
    await query.answer(f"{action}: {pillar_name.capitalize()} {emoji}")
    
    # Update message with current selection
    selected_display = ", ".join([p.capitalize() for p in selected_pillars])
    if custom_pillars:
        for cp in custom_pillars:
            if cp.lower() not in [p.lower() for p in selected_pillars]:
                continue
            selected_display += f", {cp} (custom)"
    
    message = (
        "Hello! 👋 I'm your AI Productivity Agent. My mission is to help you manage tasks, "
        "schedule commitments, and maintain productivity across work, education, and personal domains.\n\n"
        "Let's get you set up! This will only take a few minutes.\n\n"
        "First, which categories (pillars) would you like to track?\n"
        "You can select from common categories or create your own custom categories."
    )
    
    if selected_display:
        message += f"\n\n✅ Selected: {selected_display}"
    
    keyboard = get_enhanced_pillar_keyboard(selected_pillars, custom_pillars)
    await query.message.edit_text(message, reply_markup=keyboard)


async def handle_add_custom_pillar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                           session, db_user: User) -> None:
    """Handle 'Add Custom Pillar' button click."""
    query = update.callback_query
    user = update.effective_user
    
    # Move to custom pillar input state
    set_conversation_state(user.id, ConversationState.ONBOARDING_CUSTOM_PILLAR)
    
    await query.message.edit_text(
        "What would you like to name your custom category?\n\n"
        "Examples: Fitness, Side Projects, Family, Learning, etc.\n"
        "Type the name:"
    )


async def handle_pillars_done(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             session, db_user: User) -> None:
    """Handle 'Done' button after pillar selection."""
    query = update.callback_query
    user = update.effective_user
    conv_context = get_conversation_context(user.id)
    
    selected_pillars = conv_context.data.get("pillars", [])
    
    # Validate at least one pillar selected
    if not selected_pillars:
        await query.answer("Please select at least one category to continue.", show_alert=True)
        return
    
    # Store pillars and continue to work hours
    await store_pillars_and_continue(session, db_user, conv_context)
    
    # Show confirmation and move to work hours
    selected_display = "\n".join([f"• {p.capitalize()}" for p in selected_pillars])
    custom_pillars = conv_context.data.get("custom_pillars", [])
    if custom_pillars:
        selected_display += "\n" + "\n".join([f"• {p} (custom)" for p in custom_pillars])
    
    await query.message.edit_text(
        f"✅ Categories saved:\n{selected_display}\n\n"
        "You can add more categories later in Settings.\n\n"
        "What are your work hours? (e.g., 9 AM - 5 PM)\n\n"
        "You can type: '9 AM to 5 PM' or use 24-hour format: '09:00-17:00'"
    )
    
    set_conversation_state(user.id, ConversationState.ONBOARDING_WORK_HOURS)


async def handle_pillars_skip(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              session, db_user: User) -> None:
    """Handle 'Skip' button - use default pillars and continue."""
    query = update.callback_query
    user = update.effective_user
    conv_context = get_conversation_context(user.id)
    
    # Set default pillars
    conv_context.data["pillars"] = ["work"]  # Default to work
    
    # Store and continue
    await store_pillars_and_continue(session, db_user, conv_context)
    
    await query.message.edit_text(
        "✅ Using default category: Work\n\n"
        "You can add more categories later in Settings.\n\n"
        "What are your work hours? (e.g., 9 AM - 5 PM)\n\n"
        "You can type: '9 AM to 5 PM' or use 24-hour format: '09:00-17:00'"
    )
    
    set_conversation_state(user.id, ConversationState.ONBOARDING_WORK_HOURS)


async def handle_timezone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   session, db_user: User) -> None:
    """Handle timezone selection callback."""
    query = update.callback_query
    user = update.effective_user
    callback_data = query.data
    
    if callback_data == "timezone_other":
        await query.message.edit_text(
            "Please type your timezone:\n\n"
            "Examples: PST, EST, UTC, GMT+5:30, America/New_York"
        )
        return
    
    # Extract timezone (format: "timezone_PST")
    timezone = callback_data.replace("timezone_", "")
    
    # Store timezone
    db_user.timezone = timezone
    await session.commit()
    
    logger.info(f"User {user.id} set timezone: {timezone}")
    
    # Move to initial tasks
    set_conversation_state(user.id, ConversationState.ONBOARDING_INITIAL_TASKS)
    
    await query.message.edit_text(
        f"✅ Timezone saved!\n\n"
        f"Your timezone: {timezone}\n\n"
        "✅ Calendar integration is already configured!\n\n"
        "I can schedule tasks and detect conflicts with your calendar events.\n"
        "(Note: Google Calendar is pre-integrated for now. "
        "Future option to connect personal calendar will be available in Settings.)\n\n"
        "Would you like to add some initial tasks to get started?",
        reply_markup=get_yes_no_maybe_keyboard()
    )


async def handle_onboarding_yes_no(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   session, db_user: User) -> None:
    """Handle yes/no/maybe_later callbacks during onboarding."""
    query = update.callback_query
    user = update.effective_user
    callback_data = query.data
    state = get_conversation_state(user.id)
    
    if state == ConversationState.ONBOARDING_INITIAL_TASKS:
        if callback_data == "yes":
            # TODO: Implement guided task creation
            await query.message.edit_text(
                "Initial task creation coming soon! For now, let's continue.\n\n"
                "Would you like to set up any daily habits to track?"
            )
            set_conversation_state(user.id, ConversationState.ONBOARDING_HABITS)
        elif callback_data == "no" or callback_data == "maybe_later":
            await query.message.edit_text(
                "No problem! You can add tasks anytime.\n\n"
                "Would you like to set up any daily habits to track?",
                reply_markup=get_yes_no_maybe_keyboard()
            )
            set_conversation_state(user.id, ConversationState.ONBOARDING_HABITS)
    
    elif state == ConversationState.ONBOARDING_HABITS:
        if callback_data == "yes":
            # TODO: Implement guided habit creation
            await query.message.edit_text(
                "Habit creation coming soon! Let's continue.\n\n"
                "Would you like to enable mood tracking for mental health insights?"
            )
            set_conversation_state(user.id, ConversationState.ONBOARDING_MOOD_TRACKING)
        elif callback_data == "no" or callback_data == "maybe_later":
            await query.message.edit_text(
                "No problem! You can add habits anytime.\n\n"
                "Would you like to enable mood tracking for mental health insights?",
                reply_markup=get_yes_no_tellme_keyboard()
            )
            set_conversation_state(user.id, ConversationState.ONBOARDING_MOOD_TRACKING)
    
    elif state == ConversationState.ONBOARDING_MOOD_TRACKING:
        # Store mood tracking preference in context (will be added to User model later)
        conv_context = get_conversation_context(user.id)
        if callback_data == "yes":
            conv_context.data["mood_tracking_enabled"] = True
            # TODO: Add mood_tracking_enabled field to User model
            # db_user.mood_tracking_enabled = True
            await session.commit()
            await complete_onboarding(update, context, session, db_user)
        elif callback_data == "no":
            conv_context.data["mood_tracking_enabled"] = False
            # TODO: Add mood_tracking_enabled field to User model
            # db_user.mood_tracking_enabled = False
            await session.commit()
            await complete_onboarding(update, context, session, db_user)
        # "maybe_later" is handled by tell_me_more or default to no


async def handle_tell_me_more(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              session, db_user: User) -> None:
    """Handle 'Tell Me More' callback for mood tracking."""
    query = update.callback_query
    user = update.effective_user
    
    await query.message.edit_text(
        "📊 Mood Tracking:\n\n"
        "I can help you track your daily mood and provide insights on how your mood "
        "relates to your productivity and habits.\n\n"
        "Benefits:\n"
        "• Understand your mood patterns\n"
        "• See correlations with productivity\n"
        "• Identify factors that affect your well-being\n"
        "• Get personalized recommendations\n\n"
        "Would you like to enable mood tracking?",
        reply_markup=get_yes_no_tellme_keyboard()
    )

