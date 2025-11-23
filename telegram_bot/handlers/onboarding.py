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
    set_conversation_state_async,
    get_conversation_context,
    get_conversation_context_async,
    get_conversation_state,
    get_conversation_state_async
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
    
    # Pattern 1: "9 AM - 5 PM" or "9 AM to 5 PM" or "9am-5pm"
    pattern1 = r'(\d+):?(\d+)?\s*(am|pm)\s*[-to]+\s*(\d+):?(\d+)?\s*(am|pm)'
    match = re.search(pattern1, text)
    if match:
        start_hour = int(match.group(1))
        start_minute = int(match.group(2)) if match.group(2) else 0
        start_period = match.group(3)
        end_hour = int(match.group(4))
        end_minute = int(match.group(5)) if match.group(5) else 0
        end_period = match.group(6)
        
        # Convert to 24-hour format
        if start_period == 'pm' and start_hour != 12:
            start_hour += 12
        elif start_period == 'am' and start_hour == 12:
            start_hour = 0
        
        if end_period == 'pm' and end_hour != 12:
            end_hour += 12
        elif end_period == 'am' and end_hour == 12:
            end_hour = 0
        
        # For now, just return hours (minutes are stored in notes)
        return (start_hour, end_hour)
    
    # Pattern 2: "09:00-17:00" or "09:00 to 17:00" or "9:00-17:00"
    pattern2 = r'(\d{1,2}):(\d{2})\s*[-to]+\s*(\d{1,2}):(\d{2})'
    match = re.search(pattern2, text)
    if match:
        start_hour = int(match.group(1))
        end_hour = int(match.group(3))
        if 0 <= start_hour < 24 and 0 <= end_hour < 24:
            return (start_hour, end_hour)
    
    # Pattern 3: Just numbers "9 5" or "9-5" or "9 to 5"
    pattern3 = r'(\d+)\s*[-to]+\s*(\d+)'
    match = re.search(pattern3, text)
    if match:
        start_hour = int(match.group(1))
        end_hour = int(match.group(2))
        # If end < start, assume AM/PM format (e.g., 9-5 means 9 AM to 5 PM)
        if end_hour < start_hour and start_hour <= 12:
            # Likely 9 AM - 5 PM
            if end_hour <= 12:
                return (start_hour, end_hour + 12)
        elif 0 <= start_hour < 24 and 0 <= end_hour < 24:
            return (start_hour, end_hour)
    
    # Pattern 4: "Monday-Friday 9-5" or similar with day prefix
    pattern4 = r'[a-z\s,]+(\d+)\s*[-to]+\s*(\d+)'
    match = re.search(pattern4, text)
    if match:
        start_hour = int(match.group(1))
        end_hour = int(match.group(2))
        if end_hour < start_hour and start_hour <= 12:
            if end_hour <= 12:
                return (start_hour, end_hour + 12)
        elif 0 <= start_hour < 24 and 0 <= end_hour < 24:
            return (start_hour, end_hour)
    
    return None


async def handle_onboarding_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle messages during onboarding flow.
    Routes to appropriate handler based on current state.
    """
    try:
        user = update.effective_user
        text = update.message.text if update.message else ""
        
        if not text:
            await update.message.reply_text(
                "👋 Hi! I'm **Thara**, your productivity assistant.\n\n"
                "Please send a text message, or use /start to begin onboarding."
            )
            return
        
        # Use async state functions for database-backed state
        state = await get_conversation_state_async(user.id)
        conv_context = await get_conversation_context_async(user.id)
        
        logger.info("=" * 80)
        logger.info(f"📨 ONBOARDING MESSAGE")
        logger.info(f"   User: {user.id} ({user.username or 'no username'})")
        logger.info(f"   State: {state}")
        logger.info(f"   Text: '{text[:100]}...'")
        logger.info(f"   Context data keys: {list(conv_context.data.keys())}")
        logger.info("=" * 80)
        
        async with AsyncSessionLocal() as session:
            try:
                # Get user from database
                stmt = select(User).where(User.telegram_id == user.id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()
                
                if not db_user:
                    await update.message.reply_text(
                        "👋 Welcome! Please start with /start to begin onboarding."
                    )
                    return
                
                # Route based on state
                if state == ConversationState.ONBOARDING_NAME:
                    await handle_name_input(update, context, session, db_user)
                elif state == ConversationState.ONBOARDING_PILLARS:
                    await handle_pillar_selection_text(update, context, session, db_user)
                elif state == ConversationState.ONBOARDING_CUSTOM_PILLAR:
                    await handle_custom_pillar_input(update, context, session, db_user)
                elif state == ConversationState.ONBOARDING_WORK_HOURS:
                    await handle_work_hours_input(update, context, session, db_user)
                elif state == ConversationState.ONBOARDING_TIMEZONE:
                    await handle_timezone_input(update, context, session, db_user)
                elif state == ConversationState.ONBOARDING_INITIAL_TASKS:
                    await handle_initial_tasks_input(update, context, session, db_user)
                elif state == ConversationState.ONBOARDING_HABITS:
                    await handle_habits_input(update, context, session, db_user)
                elif state == ConversationState.ONBOARDING_MOOD_TRACKING:
                    await handle_mood_tracking_input(update, context, session, db_user)
                elif state == ConversationState.ONBOARDING:
                    # Default to name collection (first step)
                    await set_conversation_state_async(user.id, ConversationState.ONBOARDING_NAME)
                    await show_name_collection(update, context, session, db_user)
                else:
                    # Use AI to understand what user is saying
                    from ai.onboarding_parser import parse_onboarding_message
                    
                    try:
                        parsed = await parse_onboarding_message(text, current_step=str(state))
                        
                        # If user mentioned pillars, handle it
                        if parsed.get("pillars") and parsed.get("response_type") == "pillars":
                            await handle_pillar_selection_text(update, context, session, db_user)
                        elif parsed.get("response_type") == "work_hours" and parsed.get("work_hours"):
                            await handle_work_hours_input(update, context, session, db_user)
                        else:
                            # Generate friendly response - AI couldn't parse, guide user
                            logger.warning(f"AI parsing failed for state {state}, text: '{text[:50]}'")
                            await update.message.reply_text(
                                f"I understand you said: '{text[:100]}'\n\n"
                                "I'm here to help you complete onboarding. Could you tell me:\n"
                                "• Which categories (pillars) you want to track?\n"
                                "• Your work hours?\n"
                                "• Your timezone?\n\n"
                                "Or use /start to restart the onboarding process."
                            )
                    except Exception as ai_error:
                        logger.error(f"Error in AI parsing during onboarding: {ai_error}", exc_info=True)
                        await update.message.reply_text(
                            f"I received your message: '{text[:100]}'\n\n"
                            "I'm having trouble processing that right now. "
                            "Could you try rephrasing, or use /start to restart onboarding?"
                        )
                        
            except Exception as handler_error:
                logger.error("=" * 80)
                logger.error(f"Error in onboarding handler for state {state}: {handler_error}")
                logger.error(f"Error type: {type(handler_error).__name__}")
                logger.error(f"User: {user.id}, Text: {text[:100]}")
                logger.error("Full traceback:")
                import traceback
                logger.error(traceback.format_exc())
                logger.error("=" * 80)
                
                # Show more helpful error message
                error_msg = str(handler_error)
                if "work_hours" in error_msg.lower() or state == ConversationState.ONBOARDING_WORK_HOURS:
                    await update.message.reply_text(
                        f"⚠️ Error processing work hours: {error_msg[:100]}\n\n"
                        "Please try a simple format like: '9 AM to 5 PM'\n\n"
                        "Or use /start to restart onboarding."
                    )
                else:
                    await update.message.reply_text(
                        "⚠️ I encountered an error processing your response.\n\n"
                        "Please try again or use /start to restart onboarding.\n\n"
                        "If this persists, check the bot logs."
                    )
                
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"Fatal error in handle_onboarding_message: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"User: {update.effective_user.id if update.effective_user else 'unknown'}")
        logger.error(f"State: {get_conversation_state(update.effective_user.id) if update.effective_user else 'unknown'}")
        logger.error("Full traceback:")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        
        try:
            # Show specific error for work hours
            if "work" in str(e).lower() or get_conversation_state(update.effective_user.id) == ConversationState.ONBOARDING_WORK_HOURS:
                await update.message.reply_text(
                    f"⚠️ Error: {type(e).__name__}\n\n"
                    "Please try: '9 AM to 5 PM' or use /start to restart."
                )
            else:
                await update.message.reply_text(
                    "👋 I encountered an unexpected error.\n\n"
                    "Please try /start to restart, or send your message again."
                )
        except Exception:
            pass  # Failed to send message


async def show_name_collection(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               session: AsyncSession, db_user: User) -> None:
    """Show name collection prompt - first step of onboarding."""
    user = update.effective_user
    
    # Check if user already has a preferred name
    if db_user.preferred_name:
        # Skip to pillars if name already set
        await set_conversation_state_async(user.id, ConversationState.ONBOARDING_PILLARS)
        await show_pillar_selection(update, context, session, db_user)
        return
    
    # Suggest first name from Telegram if available
    suggested_name = user.first_name or ""
    
    message = (
        "Hello! 👋 I'm **Thara**, your AI productivity assistant.\n\n"
        "Let's get you set up! This will only take a few minutes.\n\n"
        "First, what should I call you?\n"
    )
    
    if suggested_name:
        message += f"I see your name is {suggested_name} - is that what you'd like me to use, or would you prefer something else?"
    else:
        message += "Please tell me your name (or what you'd like me to call you):"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(message)
    else:
        await update.message.reply_text(message)


async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            session: AsyncSession, db_user: User) -> None:
    """Handle name input during onboarding."""
    user = update.effective_user
    text = update.message.text.strip()
    
    # Validate name
    if not text or len(text) < 1:
        await update.message.reply_text(
            "⚠️ Please provide a valid name. What would you like me to call you?"
        )
        return
    
    if len(text) > 50:
        await update.message.reply_text(
            "⚠️ Name is too long (max 50 characters). Please provide a shorter name:"
        )
        return
    
    # Store preferred name
    db_user.preferred_name = text.strip()
    await session.commit()
    
    logger.info(f"User {user.id} set preferred name: {text}")
    
    # Move to pillar selection
    await set_conversation_state_async(user.id, ConversationState.ONBOARDING_PILLARS)
    logger.info(f"✅ State updated: ONBOARDING_NAME -> ONBOARDING_PILLARS for user {user.id}")
    
    await update.message.reply_text(
        f"Nice to meet you, {text}! 😊\n\n"
        "Now, which categories (pillars) would you like to track?\n"
        "You can select from common categories, create your own, or just tell me in natural language - I'll understand! 😊"
    )
    
    # Show pillar selection
    await show_pillar_selection(update, context, session, db_user)


async def show_pillar_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                session: AsyncSession, db_user: User) -> None:
    """Show pillar selection keyboard according to plan."""
    conv_context = get_conversation_context(update.effective_user.id)
    selected_pillars = conv_context.data.get("pillars", [])
    custom_pillars = conv_context.data.get("custom_pillars", [])
    
    user = update.effective_user
    preferred_name = db_user.preferred_name or user.first_name or "there"
    
    message = (
        f"Great, {preferred_name}! 👋\n\n"
        "My mission is to help you manage tasks, "
        "schedule commitments, and maintain productivity across work, education, and personal domains.\n\n"
        "Which categories (pillars) would you like to track?\n"
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
    
    # Validate state first (use async for database-backed state)
    current_state = await get_conversation_state_async(user.id)
    if current_state != ConversationState.ONBOARDING_WORK_HOURS:
        logger.warning(f"State mismatch for user {user.id}! Expected ONBOARDING_WORK_HOURS, got {current_state}. Fixing...")
        await set_conversation_state_async(user.id, ConversationState.ONBOARDING_WORK_HOURS)
    
    logger.info("=" * 80)
    logger.info(f"🕐 HANDLE_WORK_HOURS_INPUT")
    logger.info(f"   User: {user.id}")
    logger.info(f"   State: {current_state}")
    logger.info(f"   Input: '{text}'")
    logger.info("=" * 80)
    
    # Check for skip command
    if text.lower() in ["skip", "skip this", "later"]:
        logger.info(f"User {user.id} skipped work hours")
        set_conversation_state(user.id, ConversationState.ONBOARDING_TIMEZONE)
        await update.message.reply_text(
            "⏭️ Skipped work hours setup.\n\n"
            "What timezone are you in?\n\n"
            "Examples: PST, EST, UTC, GMT+5:30, America/New_York\n"
            "Or select from common timezones:",
            reply_markup=get_timezone_keyboard()
        )
        return
    
    # Use AI to parse work hours from natural language
    from ai.onboarding_parser import (
        parse_onboarding_message,
        normalize_time_to_24h,
        normalize_days_of_week
    )
    
    try:
        parsed = await parse_onboarding_message(text, current_step="work_hours")
        logger.info(f"AI parsing result: {parsed}")
    except Exception as e:
        logger.error(f"Error calling AI parser: {e}", exc_info=True)
        parsed = {
            "pillars": [],
            "work_hours": {},
            "timezone": None,
            "confidence": 0.0,
            "response_type": "general",
            "error": str(e)
        }
    
    work_hours_info = parsed.get("work_hours", {})
    
    # Try to extract start and end times
    start_time_str = work_hours_info.get("start_time")
    end_time_str = work_hours_info.get("end_time")
    
    logger.info(f"Extracted times from AI: start='{start_time_str}', end='{end_time_str}'")
    
    # Normalize times
    start_normalized = None
    end_normalized = None
    
    # Check if times are already in HH:MM format (24h)
    time_pattern = re.compile(r'^(\d{1,2}):(\d{2})$')
    
    if start_time_str:
        # If already in HH:MM format, validate and use directly
        match = time_pattern.match(start_time_str.strip())
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour < 24 and 0 <= minute < 60:
                start_normalized = f"{hour:02d}:{minute:02d}"
                logger.info(f"Using AI time directly (already 24h): '{start_time_str}'")
        
        # Otherwise, try to normalize
        if not start_normalized:
            try:
                start_normalized = normalize_time_to_24h(start_time_str)
                logger.info(f"Normalized start time: '{start_time_str}' -> '{start_normalized}'")
            except Exception as e:
                logger.warning(f"Error normalizing start time '{start_time_str}': {e}")
    
    if end_time_str:
        # If already in HH:MM format, validate and use directly
        match = time_pattern.match(end_time_str.strip())
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour < 24 and 0 <= minute < 60:
                end_normalized = f"{hour:02d}:{minute:02d}"
                logger.info(f"Using AI time directly (already 24h): '{end_time_str}'")
        
        # Otherwise, try to normalize
        if not end_normalized:
            try:
                end_normalized = normalize_time_to_24h(end_time_str)
                logger.info(f"Normalized end time: '{end_time_str}' -> '{end_normalized}'")
            except Exception as e:
                logger.warning(f"Error normalizing end time '{end_time_str}': {e}")
    
    # Also try fallback regex parsing if AI parsing failed
    if not start_normalized or not end_normalized:
        logger.info("AI parsing incomplete, trying fallback regex parser")
        try:
            hours = parse_work_hours(text)
            if hours:
                start_hour, end_hour = hours
                start_normalized = f"{start_hour:02d}:00"
                end_normalized = f"{end_hour:02d}:00"
                logger.info(f"Fallback parser extracted: {start_normalized} - {end_normalized}")
        except Exception as e:
            logger.warning(f"Fallback parser also failed: {e}")
    
    if not start_normalized or not end_normalized:
        # AI parsing failed, provide helpful error
        logger.warning(f"Failed to parse work hours from: '{text}' (AI confidence: {parsed.get('confidence', 0)}, work_hours_info: {work_hours_info})")
        await update.message.reply_text(
            "⚠️ I couldn't understand your work hours format. Let me help!\n\n"
            "Please provide your work hours in one of these formats:\n"
            "• '9 AM to 5 PM'\n"
            "• '9:00 AM - 5:00 PM'\n"
            "• 'Monday-Friday 9-5'\n"
            "• '09:00-17:00' (24-hour format)\n\n"
            "You can also describe complex schedules like:\n"
            "'Monday, Wednesday, Friday from 9 AM to 4 PM, with 2 hours travel time'\n\n"
            "Or type 'skip' to skip this step."
        )
        return
    
    # Extract hour from time string
    try:
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
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing normalized times '{start_normalized}' / '{end_normalized}': {e}")
        await update.message.reply_text(
            "⚠️ I had trouble processing the times. Could you try a different format?\n\n"
            "Examples: '9 AM to 5 PM' or '09:00-17:00'"
        )
        return
    
    # Store work hours (executed when validation succeeds)
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
    
    # Move to timezone (use async for database-backed state)
    await set_conversation_state_async(user.id, ConversationState.ONBOARDING_TIMEZONE)
    logger.info(f"✅ State updated: ONBOARDING_WORK_HOURS -> ONBOARDING_TIMEZONE for user {user.id}")
    
    await update.message.reply_text(
        response_msg,
        reply_markup=get_timezone_keyboard()
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
    
    # Move to initial tasks step (use async for database-backed state)
    await set_conversation_state_async(user.id, ConversationState.ONBOARDING_INITIAL_TASKS)
    logger.info(f"✅ State updated: ONBOARDING_TIMEZONE -> ONBOARDING_INITIAL_TASKS for user {user.id}")
    
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
    logger.info(f"handle_initial_tasks_input called for user {update.effective_user.id}")
    # For now, skip to habits step
    # TODO: Implement guided task creation
    await continue_to_habits(update, context, session, db_user)


async def handle_habits_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              session: AsyncSession, db_user: User) -> None:
    """Handle habits input during onboarding with fallback chain."""
    user = update.effective_user
    text = update.message.text.strip()
    
    logger.info(f"🔵 handle_habits_input: user {user.id}, text: '{text[:50]}...'")
    
    # Validate state
    current_state = get_conversation_state(user.id)
    if current_state != ConversationState.ONBOARDING_HABITS:
        logger.warning(f"State mismatch for user {user.id}! Expected ONBOARDING_HABITS, got {current_state}. Fixing...")
        set_conversation_state(user.id, ConversationState.ONBOARDING_HABITS)
    
    # Check for skip/done commands
    if text.lower() in ["skip", "done", "no", "none", "later"]:
        logger.info(f"User {user.id} skipped habits")
        set_conversation_state(user.id, ConversationState.ONBOARDING_MOOD_TRACKING)
        await update.message.reply_text(
            "⏭️ Skipped habits setup.\n\n"
            "Would you like to enable mood tracking for mental health insights?",
            reply_markup=get_yes_no_tellme_keyboard()
        )
        return
    
    # Fallback chain: Try multiple parsing strategies
    habit_name = None
    habit_description = None
    
    # Strategy 1: Direct text (simple habit name)
    if len(text.split()) <= 5:  # Likely just a habit name
        habit_name = text
        logger.info(f"Strategy 1: Direct text -> habit_name: '{habit_name}'")
    
    # Strategy 2: Try to extract with AI (if available)
    if not habit_name:
        try:
            from ai.onboarding_parser import parse_onboarding_message
            parsed = await parse_onboarding_message(text, current_step="habits")
            logger.info(f"Strategy 2: AI parsing result: {parsed}")
            
            # Extract habit info if available
            if parsed.get("response_type") == "habits" or "habit" in text.lower():
                # Try to extract habit name from text
                words = text.split()
                if words:
                    habit_name = " ".join(words[:5])  # First 5 words as habit name
        except Exception as e:
            logger.warning(f"AI parsing failed for habits: {e}")
    
    # Strategy 3: Simple extraction (last resort)
    if not habit_name:
        # Just use the text as habit name
        habit_name = text[:100]  # Limit length
        logger.info(f"Strategy 3: Using full text as habit name: '{habit_name[:50]}...'")
    
    # Store habit (for now, just acknowledge - TODO: implement Habit model storage)
    logger.info(f"✅ Extracted habit: name='{habit_name}', description='{habit_description}'")
    
    # Move to mood tracking
    set_conversation_state(user.id, ConversationState.ONBOARDING_MOOD_TRACKING)
    
    await update.message.reply_text(
        f"✅ Got it! I've noted: '{habit_name}'\n\n"
        "Habit tracking will be available soon. For now, let's continue!\n\n"
        "Would you like to enable mood tracking for mental health insights?",
        reply_markup=get_yes_no_tellme_keyboard()
    )


async def handle_mood_tracking_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    session: AsyncSession, db_user: User) -> None:
    """Handle mood tracking input during onboarding."""
    user = update.effective_user
    text = update.message.text.strip().lower()
    
    logger.info(f"🔵 handle_mood_tracking_input: user {user.id}, text: '{text[:50]}...'")
    
    # Validate state
    current_state = get_conversation_state(user.id)
    if current_state != ConversationState.ONBOARDING_MOOD_TRACKING:
        logger.warning(f"State mismatch for user {user.id}! Expected ONBOARDING_MOOD_TRACKING, got {current_state}. Fixing...")
        set_conversation_state(user.id, ConversationState.ONBOARDING_MOOD_TRACKING)
    
    # Check for yes/no responses
    if text in ["yes", "y", "enable", "ok"]:
        conv_context = get_conversation_context(user.id)
        conv_context.data["mood_tracking_enabled"] = True
        logger.info(f"User {user.id} enabled mood tracking")
        await complete_onboarding(update, context, session, db_user)
    elif text in ["no", "n", "skip", "later"]:
        conv_context = get_conversation_context(user.id)
        conv_context.data["mood_tracking_enabled"] = False
        logger.info(f"User {user.id} disabled mood tracking")
        await complete_onboarding(update, context, session, db_user)
    else:
        # Unclear response, ask for clarification
        await update.message.reply_text(
            "I didn't quite understand. Would you like to enable mood tracking?\n\n"
            "This helps track your daily mood and provides insights on how your mood "
            "relates to your productivity.\n\n"
            "Please reply with 'yes' or 'no', or use the buttons below:",
            reply_markup=get_yes_no_tellme_keyboard()
        )


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
    # Note: This is called from callback handler, so we use sync version
    set_conversation_state(db_user.telegram_id, ConversationState.ONBOARDING_WORK_HOURS)
    logger.info(f"✅ State updated: ONBOARDING_PILLARS -> ONBOARDING_WORK_HOURS for user {db_user.telegram_id}")
    
    logger.info(f"Storing pillars for user {db_user.telegram_id}: {selected_pillars}, custom: {custom_pillars}")


async def continue_to_habits(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             session: AsyncSession, db_user: User) -> None:
    """Continue to habits setup step."""
    user = update.effective_user
    await set_conversation_state_async(user.id, ConversationState.ONBOARDING_HABITS)
    logger.info(f"✅ State updated: ONBOARDING_INITIAL_TASKS -> ONBOARDING_HABITS for user {user.id}")
    
    await update.message.reply_text(
        "Would you like to set up any daily habits to track?\n\n"
        "Examples: Drink water (8 glasses/day), Exercise (30 min/day), Meditation (10 min/day)\n\n"
        "Habits help you build consistency and maintain well-being.\n\n"
        "You can type a habit name, or use the buttons below:",
        reply_markup=get_yes_no_maybe_keyboard()
    )
    # TODO: Implement habits setup


async def complete_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              session: AsyncSession, db_user: User) -> None:
    """Complete onboarding and mark user as onboarded."""
    user = update.effective_user
    
    logger.info(f"🎉 Completing onboarding for user {user.id}")
    
    db_user.is_onboarded = True
    await session.commit()
    
    await set_conversation_state_async(user.id, ConversationState.IDLE)
    logger.info(f"✅ State updated: ONBOARDING_MOOD_TRACKING -> IDLE for user {user.id}")
    
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

