"""
Comprehensive onboarding flow handler according to COMPREHENSIVE_PLAN.md
"""
import logging
import re
from typing import List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from telegram_bot.conversation import (
    ConversationState, 
    set_conversation_state, 
    get_conversation_context,
    get_conversation_state
)
from telegram_bot.keyboards import get_pillar_keyboard

logger = logging.getLogger(__name__)


def get_enhanced_pillar_keyboard(selected_pillars: List[str], custom_pillars: List[str] = None) -> InlineKeyboardMarkup:
    """
    Get enhanced pillar keyboard with Add Custom Pillar, Done, and Skip buttons.
    According to COMPREHENSIVE_PLAN.md - allows multiple selection, toggle on/off.
    """
    custom_pillars = custom_pillars or []
    
    keyboard = []
    
    # Predefined pillars with toggle indicators
    predefined_pillars = ["work", "education", "projects", "personal", "other"]
    
    # Row 1: Work, Education
    row1 = []
    for pillar in ["work", "education"]:
        emoji = "✅" if pillar in selected_pillars else ""
        row1.append(InlineKeyboardButton(
            f"{emoji} {pillar.capitalize()}", 
            callback_data=f"pillar_toggle_{pillar}"
        ))
    keyboard.append(row1)
    
    # Row 2: Projects, Personal
    row2 = []
    for pillar in ["projects", "personal"]:
        emoji = "✅" if pillar in selected_pillars else ""
        row2.append(InlineKeyboardButton(
            f"{emoji} {pillar.capitalize()}", 
            callback_data=f"pillar_toggle_{pillar}"
        ))
    keyboard.append(row2)
    
    # Row 3: Other
    row3 = []
    emoji = "✅" if "other" in selected_pillars else ""
    row3.append(InlineKeyboardButton(
        f"{emoji} Other", 
        callback_data=f"pillar_toggle_other"
    ))
    keyboard.append(row3)
    
    # Custom pillars row
    if custom_pillars:
        custom_row = []
        for custom_pillar in custom_pillars[:2]:  # Show max 2 custom pillars per row
            emoji = "✅" if custom_pillar.lower() in [p.lower() for p in selected_pillars] else ""
            custom_row.append(InlineKeyboardButton(
                f"{emoji} {custom_pillar} (custom)", 
                callback_data=f"pillar_toggle_{custom_pillar}"
            ))
        if len(custom_row) > 0:
            keyboard.append(custom_row)
    
    # Action buttons row
    keyboard.append([
        InlineKeyboardButton("➕ Add Custom Pillar", callback_data="onboarding_add_custom_pillar"),
    ])
    keyboard.append([
        InlineKeyboardButton("✅ Done", callback_data="onboarding_pillars_done"),
        InlineKeyboardButton("⏭️ Skip", callback_data="onboarding_pillars_skip"),
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_timezone_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for common timezones."""
    keyboard = [
        [
            InlineKeyboardButton("PST", callback_data="timezone_PST"),
            InlineKeyboardButton("EST", callback_data="timezone_EST"),
        ],
        [
            InlineKeyboardButton("CST", callback_data="timezone_CST"),
            InlineKeyboardButton("MST", callback_data="timezone_MST"),
        ],
        [
            InlineKeyboardButton("UTC", callback_data="timezone_UTC"),
        ],
        [
            InlineKeyboardButton("Other (Type manually)", callback_data="timezone_other"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_maybe_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with Yes, No, Maybe Later options."""
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="yes"),
            InlineKeyboardButton("No", callback_data="no"),
        ],
        [
            InlineKeyboardButton("Maybe Later", callback_data="maybe_later"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_tellme_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with Yes, No, Tell Me More options."""
    keyboard = [
        [
            InlineKeyboardButton("Yes, Enable", callback_data="yes"),
            InlineKeyboardButton("No, Skip", callback_data="no"),
        ],
        [
            InlineKeyboardButton("Tell Me More", callback_data="tell_me_more"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def parse_work_hours(text: str) -> Optional[tuple]:
    """
    Parse work hours from natural language text.
    Returns (start_hour, end_hour) in 24-hour format, or None if parsing fails.
    """
    text = text.lower().strip()
    
    # Pattern 1: "9 AM - 5 PM" or "9 AM to 5 PM"
    pattern1 = r'(\d+)\s*(am|pm)\s*[-to]+\s*(\d+)\s*(am|pm)'
    match = re.search(pattern1, text)
    if match:
        start_hour = int(match.group(1))
        start_period = match.group(2)
        end_hour = int(match.group(3))
        end_period = match.group(4)
        
        # Convert to 24-hour format
        if start_period == 'pm' and start_hour != 12:
            start_hour += 12
        if start_period == 'am' and start_hour == 12:
            start_hour = 0
        
        if end_period == 'pm' and end_hour != 12:
            end_hour += 12
        if end_period == 'am' and end_hour == 12:
            end_hour = 0
        
        return (start_hour, end_hour)
    
    # Pattern 2: "09:00-17:00" or "09:00 to 17:00"
    pattern2 = r'(\d{1,2}):\d{2}\s*[-to]+\s*(\d{1,2}):\d{2}'
    match = re.search(pattern2, text)
    if match:
        start_hour = int(match.group(1))
        end_hour = int(match.group(2))
        if 0 <= start_hour < 24 and 0 <= end_hour < 24:
            return (start_hour, end_hour)
    
    # Pattern 3: Just numbers "9 5" or "9-5"
    pattern3 = r'(\d+)\s*[-to]+\s*(\d+)'
    match = re.search(pattern3, text)
    if match:
        start_hour = int(match.group(1))
        end_hour = int(match.group(2))
        # Assume 24-hour format if end < start, otherwise assume AM/PM
        if end_hour < start_hour:
            # Likely 9 AM - 5 PM
            return (start_hour, end_hour + 12)
        elif 0 <= start_hour < 24 and 0 <= end_hour < 24:
            return (start_hour, end_hour)
    
    return None


async def handle_onboarding_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle messages during onboarding flow.
    Routes to appropriate handler based on current state.
    """
    user = update.effective_user
    text = update.message.text if update.message else ""
    state = get_conversation_state(user.id)
    conv_context = get_conversation_context(user.id)
    
    logger.info(f"Onboarding message from user {user.id}, state: {state}, text: {text[:50]}")
    
    async with AsyncSessionLocal() as session:
        # Get user from database
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await update.message.reply_text("Please start with /start first.")
            return
        
        # Route based on state
        if state == ConversationState.ONBOARDING_PILLARS:
            await handle_pillar_selection_text(update, context, session, db_user)
        elif state == ConversationState.ONBOARDING_CUSTOM_PILLAR:
            await handle_custom_pillar_input(update, context, session, db_user)
        elif state == ConversationState.ONBOARDING_WORK_HOURS:
            await handle_work_hours_input(update, context, session, db_user)
        elif state == ConversationState.ONBOARDING_TIMEZONE:
            await handle_timezone_input(update, context, session, db_user)
        elif state == ConversationState.ONBOARDING_TASKS:
            # Initial tasks setup - can be handled later
            await handle_initial_tasks_input(update, context, session, db_user)
        elif state == ConversationState.ONBOARDING:
            # Default to pillar selection
            set_conversation_state(user.id, ConversationState.ONBOARDING_PILLARS)
            await show_pillar_selection(update, context, session, db_user)
        else:
            # Use AI to understand what user is saying
            from ai.onboarding_parser import parse_onboarding_message
            parsed = await parse_onboarding_message(text, current_step=str(state))
            
            # If user mentioned pillars, handle it
            if parsed.get("pillars") and parsed.get("response_type") == "pillars":
                await handle_pillar_selection_text(update, context, session, db_user)
            elif parsed.get("response_type") == "work_hours" and parsed.get("work_hours"):
                await handle_work_hours_input(update, context, session, db_user)
            else:
                # Generate friendly response
                await update.message.reply_text(
                    "I'm **Thara**! 😊 I understand you're trying to tell me something.\n\n"
                    "You can use the buttons below, or just tell me naturally what you need - I'll understand!\n\n"
                    "Or type /start to restart onboarding if you'd like."
                )


async def show_pillar_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                session: AsyncSession, db_user: User) -> None:
    """Show pillar selection keyboard according to plan."""
    conv_context = get_conversation_context(update.effective_user.id)
    selected_pillars = conv_context.data.get("pillars", [])
    custom_pillars = conv_context.data.get("custom_pillars", [])
    
    message = (
        "Hello! 👋 I'm **Thara**, your AI productivity assistant. My mission is to help you manage tasks, "
        "schedule commitments, and maintain productivity across work, education, and personal domains.\n\n"
        "Let's get you set up! This will only take a few minutes.\n\n"
        "First, which categories (pillars) would you like to track?\n"
        "You can select from common categories, create your own, or just tell me in natural language - I'll understand! 😊"
    )
    
    keyboard = get_enhanced_pillar_keyboard(selected_pillars, custom_pillars)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(message, reply_markup=keyboard)
    else:
        await update.message.reply_text(message, reply_markup=keyboard)


async def handle_pillar_selection_text(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                       session: AsyncSession, db_user: User) -> None:
    """Handle text input during pillar selection - uses AI to understand natural language."""
    text = update.message.text.strip()
    user = update.effective_user
    conv_context = get_conversation_context(user.id)
    
    # Check if user said "done"
    if text.lower() == "done":
        selected_pillars = conv_context.data.get("pillars", [])
        if not selected_pillars:
            await update.message.reply_text(
                "Please select at least one category to continue.",
                reply_markup=get_enhanced_pillar_keyboard(selected_pillars, 
                                                         conv_context.data.get("custom_pillars", []))
            )
            return
        
        # Store pillars and move to work hours
        await store_pillars_and_continue(session, db_user, conv_context)
        return
    
    # Use AI to understand what user is saying about pillars
    from ai.onboarding_parser import parse_onboarding_message
    
    parsed = await parse_onboarding_message(text, current_step="pillars")
    
    if parsed.get("response_type") == "pillars" and parsed.get("pillars"):
        # User mentioned pillars in natural language
        mentioned_pillars = [p.lower() for p in parsed["pillars"]]
        selected_pillars = conv_context.data.get("pillars", [])
        
        # Add mentioned pillars if not already selected
        for pillar in mentioned_pillars:
            if pillar not in [p.lower() for p in selected_pillars]:
                # Check if it's a predefined pillar
                predefined = ["work", "education", "projects", "personal", "other"]
                if pillar.lower() in predefined:
                    if pillar.lower() not in selected_pillars:
                        selected_pillars.append(pillar.lower())
                else:
                    # Custom pillar
                    custom_pillars = conv_context.data.get("custom_pillars", [])
                    if pillar.title() not in custom_pillars:
                        if "custom_pillars" not in conv_context.data:
                            conv_context.data["custom_pillars"] = []
                        conv_context.data["custom_pillars"].append(pillar.title())
                        if pillar.title() not in selected_pillars:
                            selected_pillars.append(pillar.title())
        
        conv_context.data["pillars"] = selected_pillars
        
        # Show updated selection
        selected_display = []
        for p in selected_pillars:
            if p.lower() in ["work", "education", "projects", "personal", "other"]:
                selected_display.append(f"• {p.capitalize()}")
            else:
                selected_display.append(f"• {p} (custom)")
        
        await update.message.reply_text(
            f"✅ Got it! I've added the categories you mentioned.\n\n"
            f"Current categories:\n" + "\n".join(selected_display) + "\n\n"
            "You can select more using the buttons below, or type 'done' when finished.",
            reply_markup=get_enhanced_pillar_keyboard(selected_pillars, 
                                                     conv_context.data.get("custom_pillars", []))
        )
    else:
        # General message - acknowledge but guide them
        await update.message.reply_text(
            "I understand you're telling me about categories. You can:\n"
            "- Use the buttons to select categories\n"
            "- Tell me category names (like 'work', 'education', etc.)\n"
            "- Type 'done' when finished\n\n"
            "Or just use the buttons - they make it easier! 😊",
            reply_markup=get_enhanced_pillar_keyboard(conv_context.data.get("pillars", []), 
                                                     conv_context.data.get("custom_pillars", []))
        )


async def handle_custom_pillar_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     session: AsyncSession, db_user: User) -> None:
    """Handle custom pillar name input."""
    user = update.effective_user
    text = update.message.text.strip()
    conv_context = get_conversation_context(user.id)
    
    # Validate custom pillar name
    if len(text) > 50:
        await update.message.reply_text(
            "⚠️ Category name is too long (max 50 characters). Please try a shorter name:"
        )
        return
    
    if not text or not text.strip():
        await update.message.reply_text(
            "⚠️ Please provide a valid category name. Examples: Fitness, Side Projects, Family, Learning, etc.\n\n"
            "Type the name:"
        )
        return
    
    # Normalize name
    pillar_name = text.strip().title()
    
    # Check for duplicates (predefined + custom)
    selected_pillars = conv_context.data.get("pillars", [])
    custom_pillars = conv_context.data.get("custom_pillars", [])
    
    all_pillars = [p.lower() for p in selected_pillars + custom_pillars]
    if pillar_name.lower() in all_pillars:
        await update.message.reply_text(
            f"⚠️ You already have '{pillar_name}' category. Please choose a different name.\n\n"
            "Type a new category name:"
        )
        return
    
    # Add custom pillar
    if "custom_pillars" not in conv_context.data:
        conv_context.data["custom_pillars"] = []
    
    if pillar_name not in conv_context.data["custom_pillars"]:
        conv_context.data["custom_pillars"].append(pillar_name)
    
    # Show updated list
    selected_pillars_display = []
    for p in conv_context.data.get("pillars", []):
        selected_pillars_display.append(f"• {p.capitalize()}")
    for p in conv_context.data["custom_pillars"]:
        selected_pillars_display.append(f"• {p} (custom)")
    
    await update.message.reply_text(
        f"✅ Added custom category: '{pillar_name}'\n\n"
        f"Current categories:\n" + "\n".join(selected_pillars_display) + "\n\n"
        "Select more categories or [Done] to continue:",
        reply_markup=get_enhanced_pillar_keyboard(
            conv_context.data.get("pillars", []),
            conv_context.data.get("custom_pillars", [])
        )
    )
    
    # Return to pillar selection state
    set_conversation_state(user.id, ConversationState.ONBOARDING_PILLARS)


async def handle_work_hours_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  session: AsyncSession, db_user: User) -> None:
    """Handle work hours input - uses AI to understand natural language schedules."""
    user = update.effective_user
    text = update.message.text.strip()
    
    # Use AI to parse work hours from natural language
    from ai.onboarding_parser import (
        parse_onboarding_message,
        normalize_time_to_24h,
        normalize_days_of_week
    )
    
    parsed = await parse_onboarding_message(text, current_step="work_hours")
    
    work_hours_info = parsed.get("work_hours", {})
    
    # Try to extract start and end times
    start_time_str = work_hours_info.get("start_time")
    end_time_str = work_hours_info.get("end_time")
    
    # Normalize times
    start_normalized = normalize_time_to_24h(start_time_str) if start_time_str else None
    end_normalized = normalize_time_to_24h(end_time_str) if end_time_str else None
    
    # Also try fallback regex parsing
    if not start_normalized or not end_normalized:
        hours = parse_work_hours(text)
        if hours:
            start_hour, end_hour = hours
            start_normalized = f"{start_hour:02d}:00"
            end_normalized = f"{end_hour:02d}:00"
    
    if start_normalized and end_normalized:
        # Extract hour from time string
        start_hour = int(start_normalized.split(":")[0])
        end_hour = int(end_normalized.split(":")[0])
        
        # Validate hours
        if not (0 <= start_hour < 24 and 0 <= end_hour < 24):
            await update.message.reply_text(
                "⚠️ I extracted some times, but they seem invalid. Could you clarify your work hours?\n\n"
                "Examples: '9 AM to 5 PM' or 'Monday-Friday 9-5'"
            )
            return
        
        if start_hour >= end_hour:
            await update.message.reply_text(
                "⚠️ Start time should be before end time. Could you clarify?\n\n"
                "Examples: '9 AM to 5 PM' or 'Monday-Friday 9-5'"
            )
            return
        
        # Store work hours
        db_user.work_start_hour = start_hour
        db_user.work_end_hour = end_hour
        
        # Store additional notes (travel time, classes, etc.)
        notes = work_hours_info.get("notes", "")
        if notes:
            # Store notes in user metadata if available
            if not hasattr(db_user, 'metadata') or db_user.metadata is None:
                db_user.metadata = {}
            db_user.metadata['work_hours_notes'] = notes
        
        await session.commit()
        
        logger.info(f"User {user.id} set work hours: {start_hour}:00 - {end_hour}:00 (AI parsed)")
        
        # Build response message
        response_msg = f"✅ Work hours saved!\n\n"
        response_msg += f"Your work hours: {start_hour}:00 - {end_hour}:00\n"
        
        days = work_hours_info.get("days", [])
        if days:
            normalized_days = normalize_days_of_week(days)
            if normalized_days:
                days_display = ", ".join([d.capitalize() for d in normalized_days])
                response_msg += f"Days: {days_display}\n"
        
        if notes:
            response_msg += f"\n📝 Note: {notes}\n"
        
        response_msg += "\nWhat timezone are you in?\n\n"
        response_msg += "Examples: PST, EST, UTC, GMT+5:30, America/New_York\n"
        response_msg += "Or select from common timezones:"
        
        # Move to timezone
        set_conversation_state(user.id, ConversationState.ONBOARDING_TIMEZONE)
        
        await update.message.reply_text(
            response_msg,
            reply_markup=get_timezone_keyboard()
        )
    else:
        # Couldn't parse - ask for clarification
        await update.message.reply_text(
            "I'm having trouble understanding your work hours. Could you tell me in a simpler format?\n\n"
            "Examples:\n"
            "- '9 AM to 5 PM'\n"
            "- 'Monday to Friday, 9 AM - 5 PM'\n"
            "- '9:00-17:00'\n\n"
            "Or feel free to describe it however you like - I'll do my best to understand! 😊"
        )


async def handle_timezone_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                session: AsyncSession, db_user: User) -> None:
    """Handle timezone input."""
    user = update.effective_user
    text = update.message.text.strip()
    
    # For now, accept any timezone string (can add validation later)
    db_user.timezone = text if text else "UTC"
    await session.commit()
    
    logger.info(f"User {user.id} set timezone: {text}")
    
    # Move to initial tasks step
    set_conversation_state(user.id, ConversationState.ONBOARDING_TASKS)
    
    await update.message.reply_text(
        "✅ Timezone saved!\n\n"
        f"Your timezone: {text}\n\n"
        "✅ Calendar integration is already configured!\n\n"
        "I can schedule tasks and detect conflicts with your calendar events.\n"
        "(Note: Google Calendar is pre-integrated for now. "
        "Future option to connect personal calendar will be available in Settings.)\n\n"
        "Would you like to add some initial tasks to get started?",
        reply_markup=get_yes_no_maybe_keyboard()
    )


async def handle_initial_tasks_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     session: AsyncSession, db_user: User) -> None:
    """Handle initial tasks setup (optional step)."""
    # For now, skip to habits step
    # TODO: Implement guided task creation
    await continue_to_habits(update, context, session, db_user)


async def store_pillars_and_continue(session: AsyncSession, db_user: User, 
                                     conv_context) -> None:
    """
    Store selected pillars and move to work hours step.
    Note: Message sending is handled by the callback handler that calls this function.
    """
    selected_pillars = conv_context.data.get("pillars", [])
    custom_pillars = conv_context.data.get("custom_pillars", [])
    
    # Store custom pillars in user's metadata (we'll need to add this field or use a JSON field)
    # For now, store in conversation context - will persist in database later
    # TODO: Add custom_pillars JSON field to User model
    
    # Move to work hours (actual message is sent by the callback handler)
    set_conversation_state(db_user.telegram_id, ConversationState.ONBOARDING_WORK_HOURS)
    
    logger.info(f"Storing pillars for user {db_user.telegram_id}: {selected_pillars}, custom: {custom_pillars}")


async def continue_to_habits(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             session: AsyncSession, db_user: User) -> None:
    """Continue to habits setup step."""
    user = update.effective_user
    set_conversation_state(user.id, ConversationState.ONBOARDING)
    
    await update.message.reply_text(
        "Would you like to set up any daily habits to track?\n\n"
        "Examples: Drink water (8 glasses/day), Exercise (30 min/day), Meditation (10 min/day)\n\n"
        "Habits help you build consistency and maintain well-being.\n\n",
        reply_markup=get_yes_no_maybe_keyboard()
    )
    # TODO: Implement habits setup


async def complete_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              session: AsyncSession, db_user: User) -> None:
    """Complete onboarding and mark user as onboarded."""
    user = update.effective_user
    
    db_user.is_onboarded = True
    await session.commit()
    
    set_conversation_state(user.id, ConversationState.IDLE)
    
    completion_message = (
        "🎉 Welcome! I'm **Thara**, your AI productivity assistant!\n\n"
        "You're all set up and ready to go. Here's what you can do:\n\n"
        "📋 Tasks: Create and manage tasks naturally\n"
        "📅 Calendar: View and schedule your commitments\n"
        "🤖 AI Assistant: I'll help prioritize and suggest actions\n"
        "📊 Insights: Get daily summaries and weekly reviews\n\n"
        "Try saying: 'Add task: Prepare presentation for client meeting'\n"
        "Or use /help to see all commands.\n\n"
        "Just talk to me naturally - I'll understand! 😊\n\n"
        "Let's make you more productive! 🚀"
    )
    
    if update.callback_query:
        await update.callback_query.message.edit_text(completion_message)
    elif update.message:
        await update.message.reply_text(completion_message)
    
    logger.info(f"User {user.id} completed onboarding")

