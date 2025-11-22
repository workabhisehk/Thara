"""
Natural language task creation handler according to COMPREHENSIVE_PLAN.md Section 2.1
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.models import User, Task, TaskStatus, TaskPriority
from sqlalchemy import select
from telegram_bot.conversation import (
    ConversationState,
    get_conversation_state,
    get_conversation_context,
    set_conversation_state,
    clear_conversation_context,
)
from ai.intent_extraction import extract_intent, categorize_task
from ai.task_entity_extraction import extract_task_entities
from tasks.service import create_task
from telegram_bot.keyboards import get_yes_no_keyboard, get_pillar_keyboard, get_priority_keyboard, get_confirmation_keyboard

logger = logging.getLogger(__name__)


async def handle_natural_language_task_creation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    intent_result: dict
) -> None:
    """
    Handle natural language task creation flow according to COMPREHENSIVE_PLAN.md.
    
    Flow:
    1. Extract intent and entities
    2. Categorize task with AI
    3. Ask for confirmation
    4. Collect missing information (priority, due date, duration)
    5. Create task
    """
    user = update.effective_user
    entities = intent_result.get("entities", {})
    confidence = intent_result.get("confidence", 0.5)
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user or not db_user.is_onboarded:
            await update.message.reply_text("Please complete onboarding first. Use /start to begin.")
            return
        
        # Extract task title from entities
        task_title = entities.get("task") or entities.get("task_title") or ""
        
        if not task_title:
            await update.message.reply_text(
                "I understand you want to create a task, but I couldn't extract the task description.\n\n"
                "Please try: 'Add task: [your task description]'"
            )
            return
        
        # Store in conversation context for task creation flow
        conv_context = get_conversation_context(user.id)
        conv_context.data["task_title"] = task_title
        conv_context.data["nl_task_creation"] = True  # Flag for natural language flow
        
        # Get user's available pillars (predefined + custom)
        available_pillars = ["work", "education", "projects", "personal", "other"]
        # TODO: Get custom pillars from User model when custom_pillars field is added
        # For now, get from conversation context (stored during onboarding)
        custom_pillars = conv_context.data.get("custom_pillars", [])
        available_pillars.extend([p.lower() for p in custom_pillars])
        
        # AI categorization with confidence
        if confidence >= 0.7:
            # Only categorize if intent extraction was confident
            categorization_result = await categorize_task(
                task_title,
                db_user.id,
                session,
                available_pillars=available_pillars
            )
            
            suggested_pillar = categorization_result.get("pillar", "other")
            cat_confidence = categorization_result.get("confidence", 0.5)
            reasoning = categorization_result.get("reasoning", "")
            
            # Extract entities from message
            task_entities = await extract_task_entities(
                update.message.text,
                db_user.id,
                session
            )
            
            # Merge extracted entities
            if task_entities.get("priority"):
                conv_context.data["task_priority"] = task_entities["priority"]
            if task_entities.get("due_date"):
                conv_context.data["task_due_date"] = task_entities["due_date"]
            if task_entities.get("estimated_duration"):
                conv_context.data["task_duration"] = task_entities["estimated_duration"]
            if task_entities.get("description"):
                conv_context.data["task_description"] = task_entities["description"]
            
            # Store suggested pillar (mark as AI suggestion for correction tracking)
            conv_context.data["task_pillar"] = suggested_pillar
            conv_context.data["original_suggested_pillar"] = suggested_pillar  # For learning
            conv_context.data["original_suggested_priority"] = task_entities.get("priority")  # For learning
            
            # Show confirmation with categorization
            await show_task_confirmation(update, context, session, db_user, cat_confidence)
        else:
            # Low confidence - ask user to clarify
            await update.message.reply_text(
                f"I think you want to create a task: **{task_title}**\n\n"
                "Is this correct?",
                parse_mode="Markdown",
                reply_markup=get_yes_no_keyboard()
            )
            set_conversation_state(user.id, ConversationState.ADDING_TASK)


async def show_task_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session,
    db_user: User,
    confidence: float
) -> None:
    """Show task confirmation with AI categorization."""
    user = update.effective_user
    conv_context = get_conversation_context(user.id)
    
    task_title = conv_context.data.get("task_title", "")
    suggested_pillar = conv_context.data.get("task_pillar", "other")
    task_priority = conv_context.data.get("task_priority")
    task_due_date = conv_context.data.get("task_due_date")
    task_duration = conv_context.data.get("task_duration")
    
    # Build confirmation message
    message = f"📋 **Task: {task_title}**\n"
    message += f"Category: **{suggested_pillar.capitalize()}**"
    
    if confidence < 0.7:
        message += f" (confidence: {confidence:.0%})"
    
    message += "\n\n"
    
    if task_priority:
        message += f"Priority: {task_priority.capitalize()}\n"
    if task_due_date:
        message += f"Due: {task_due_date.strftime('%Y-%m-%d')}\n"
    if task_duration:
        hours = task_duration // 60
        minutes = task_duration % 60
        if hours > 0:
            message += f"Duration: {hours}h {minutes}m\n"
        else:
            message += f"Duration: {minutes}m\n"
    
    message += "\nIs this correct?"
    
    # Create keyboard with options
    keyboard = []
    
    # Yes/No buttons
    keyboard.append([
        InlineKeyboardButton("✅ Yes, Create", callback_data="nl_task_confirm"),
        InlineKeyboardButton("❌ No, Cancel", callback_data="nl_task_cancel"),
    ])
    
    # Edit options
    if confidence < 0.7 or suggested_pillar == "other":
        keyboard.append([
            InlineKeyboardButton("✏️ Change Category", callback_data="nl_task_change_pillar"),
        ])
    
    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_nl_task_callbacks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle natural language task creation callbacks."""
    query = update.callback_query
    callback_data = query.data
    user = update.effective_user
    
    # Acknowledge callback immediately
    await query.answer()
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await query.message.reply_text("Please start with /start first.")
            return
        
        conv_context = get_conversation_context(user.id)
        
        if callback_data == "nl_task_confirm":
            # Create task
            task_title = conv_context.data.get("task_title", "")
            pillar = conv_context.data.get("task_pillar", "other")
            priority = conv_context.data.get("task_priority", "medium")
            due_date = conv_context.data.get("task_due_date")
            duration = conv_context.data.get("task_duration")
            description = conv_context.data.get("task_description")
            
            # Check if we have all required info or need to collect more
            if not priority:
                # Ask for priority
                set_conversation_state(user.id, ConversationState.ADDING_TASK_PRIORITY)
                await query.message.edit_text(
                    f"✅ Category confirmed: **{pillar.capitalize()}**\n\n"
                    "What's the priority?",
                    parse_mode="Markdown",
                    reply_markup=get_priority_keyboard()
                )
                return
            
            # Create task
            task = await create_task(
                session,
                db_user.id,
                title=task_title,
                description=description,
                pillar=pillar,
                priority=priority,
                due_date=due_date,
                estimated_duration=duration
            )
            
            await session.commit()
            
            await query.answer("✅ Task created!")
            await query.message.edit_text(
                f"✅ **Task created!**\n\n"
                f"**{task.title}**\n\n"
                "I'll remind you before the deadline.",
                parse_mode="Markdown"
            )
            
            # Clear context
            clear_conversation_context(user.id)
            logger.info(f"User {user.id} created task {task.id} via natural language: {task.title}")
            
        elif callback_data == "nl_task_cancel":
            await query.answer("❌ Cancelled")
            await query.message.edit_text("❌ Task creation cancelled.")
            clear_conversation_context(user.id)
            
        elif callback_data == "nl_task_change_pillar":
            # Show pillar selection - Track this as a correction
            original_pillar = conv_context.data.get("task_pillar", "other")
            
            # Store original for learning (will track correction when new pillar selected)
            conv_context.data["original_suggested_pillar"] = original_pillar
            conv_context.data["task_description"] = conv_context.data.get("task_title", "")
            
            available_pillars = ["work", "education", "projects", "personal", "other"]
            custom_pillars = conv_context.data.get("custom_pillars", [])
            # TODO: Include custom pillars in keyboard
            
            await query.message.edit_text(
                "Select the category for this task:",
                reply_markup=get_pillar_keyboard()
            )
            set_conversation_state(user.id, ConversationState.ADDING_TASK_PILLAR)

