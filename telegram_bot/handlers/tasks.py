"""
Task management handlers according to COMPREHENSIVE_PLAN.md
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import Task, User, TaskStatus, TaskPriority, PillarType
from sqlalchemy import select, and_, or_
from telegram_bot.conversation import ConversationState, set_conversation_state, get_conversation_context, get_conversation_state
from tasks.service import create_task, get_tasks, get_task, update_task, delete_task, complete_task

logger = logging.getLogger(__name__)


def get_tasks_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main tasks menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Task", callback_data="task_add"),
            InlineKeyboardButton("📋 View All", callback_data="task_view_all"),
        ],
        [
            InlineKeyboardButton("🔍 Filter", callback_data="task_filter_menu"),
            InlineKeyboardButton("🔀 Sort", callback_data="task_sort_menu"),
        ],
        [
            InlineKeyboardButton("📊 Statistics", callback_data="task_stats"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_filter_keyboard() -> InlineKeyboardMarkup:
    """Get filter options keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("By Priority", callback_data="filter_priority"),
            InlineKeyboardButton("By Pillar", callback_data="filter_pillar"),
        ],
        [
            InlineKeyboardButton("By Status", callback_data="filter_status"),
            InlineKeyboardButton("By Due Date", callback_data="filter_due_date"),
        ],
        [
            InlineKeyboardButton("Clear Filters", callback_data="filter_clear"),
            InlineKeyboardButton("Back", callback_data="task_menu"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_pillar_filter_keyboard(selected_pillars: List[str] = None) -> InlineKeyboardMarkup:
    """Get pillar filter keyboard with user's available pillars."""
    selected_pillars = selected_pillars or []
    keyboard = []
    
    # Predefined pillars
    predefined = ["work", "education", "projects", "personal", "other"]
    
    row = []
    for pillar in predefined[:2]:
        emoji = "✅" if pillar in selected_pillars else ""
        row.append(InlineKeyboardButton(
            f"{emoji} {pillar.capitalize()}", 
            callback_data=f"filter_pillar_{pillar}"
        ))
    keyboard.append(row)
    
    row = []
    for pillar in predefined[2:4]:
        emoji = "✅" if pillar in selected_pillars else ""
        row.append(InlineKeyboardButton(
            f"{emoji} {pillar.capitalize()}", 
            callback_data=f"filter_pillar_{pillar}"
        ))
    keyboard.append(row)
    
    row = []
    emoji = "✅" if "other" in selected_pillars else ""
    row.append(InlineKeyboardButton(
        f"{emoji} Other", 
        callback_data="filter_pillar_other"
    ))
    keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton("Apply Filter", callback_data="filter_apply_pillar"),
        InlineKeyboardButton("Back", callback_data="task_filter_menu"),
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_priority_filter_keyboard() -> InlineKeyboardMarkup:
    """Get priority filter keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔴 High", callback_data="filter_priority_high"),
            InlineKeyboardButton("🟡 Medium", callback_data="filter_priority_medium"),
            InlineKeyboardButton("🟢 Low", callback_data="filter_priority_low"),
        ],
        [
            InlineKeyboardButton("Apply Filter", callback_data="filter_apply_priority"),
            InlineKeyboardButton("Back", callback_data="task_filter_menu"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_status_filter_keyboard() -> InlineKeyboardMarkup:
    """Get status filter keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("Pending", callback_data="filter_status_pending"),
            InlineKeyboardButton("In Progress", callback_data="filter_status_in_progress"),
        ],
        [
            InlineKeyboardButton("Completed", callback_data="filter_status_completed"),
            InlineKeyboardButton("Overdue", callback_data="filter_status_overdue"),
        ],
        [
            InlineKeyboardButton("Apply Filter", callback_data="filter_apply_status"),
            InlineKeyboardButton("Back", callback_data="task_filter_menu"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_due_date_filter_keyboard() -> InlineKeyboardMarkup:
    """Get due date filter keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("Overdue", callback_data="filter_due_overdue"),
            InlineKeyboardButton("Today", callback_data="filter_due_today"),
        ],
        [
            InlineKeyboardButton("Tomorrow", callback_data="filter_due_tomorrow"),
            InlineKeyboardButton("This Week", callback_data="filter_due_week"),
        ],
        [
            InlineKeyboardButton("No Due Date", callback_data="filter_due_none"),
            InlineKeyboardButton("Back", callback_data="task_filter_menu"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_sort_keyboard() -> InlineKeyboardMarkup:
    """Get sort options keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("By Priority", callback_data="sort_priority"),
            InlineKeyboardButton("By Due Date", callback_data="sort_due_date"),
        ],
        [
            InlineKeyboardButton("By Created Date", callback_data="sort_created"),
            InlineKeyboardButton("By Pillar", callback_data="sort_pillar"),
        ],
        [
            InlineKeyboardButton("Back", callback_data="task_menu"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def format_task_list(tasks: List[Task], group_by: str = "priority") -> str:
    """
    Format task list according to COMPREHENSIVE_PLAN.md.
    Groups by priority, pillar, or due date.
    """
    if not tasks:
        return "📋 You don't have any tasks matching this filter.\n\nUse 'Add Task' to create a new task!"
    
    # Priority emoji mapping
    priority_emoji = {
        TaskPriority.URGENT: "🔴",
        TaskPriority.HIGH: "🔴",
        TaskPriority.MEDIUM: "🟡",
        TaskPriority.LOW: "🟢",
    }
    
    # Status emoji mapping
    status_emoji = {
        TaskStatus.PENDING: "⏳",
        TaskStatus.IN_PROGRESS: "🔄",
        TaskStatus.COMPLETED: "✅",
        TaskStatus.OVERDUE: "⚠️",
    }
    
    if group_by == "priority":
        # Group by priority
        tasks_by_priority = {}
        for task in tasks:
            priority_key = task.priority.value.capitalize()
            if priority_key not in tasks_by_priority:
                tasks_by_priority[priority_key] = []
            tasks_by_priority[priority_key].append(task)
        
        message = "📋 **Your Active Tasks:**\n\n"
        for priority in ["Urgent", "High", "Medium", "Low"]:
            if priority in tasks_by_priority:
                emoji = priority_emoji.get(getattr(TaskPriority, priority.upper(), None), "⚪")
                message += f"{emoji} **{priority.upper()} PRIORITY** ({len(tasks_by_priority[priority])})\n"
                for i, task in enumerate(tasks_by_priority[priority], 1):
                    due_str = ""
                    if task.due_date:
                        due_str = f" (due: {task.due_date.strftime('%Y-%m-%d')})"
                    message += f"  {i}. {task.title}{due_str}\n"
                message += "\n"
        
        return message
    
    elif group_by == "pillar":
        # Group by pillar
        tasks_by_pillar = {}
        for task in tasks:
            pillar_key = task.pillar.value.capitalize()
            if pillar_key not in tasks_by_pillar:
                tasks_by_pillar[pillar_key] = []
            tasks_by_pillar[pillar_key].append(task)
        
        message = "📋 **Your Tasks by Category:**\n\n"
        for pillar in sorted(tasks_by_pillar.keys()):
            message += f"**{pillar.upper()}** ({len(tasks_by_pillar[pillar])})\n"
            for i, task in enumerate(tasks_by_pillar[pillar], 1):
                priority_icon = priority_emoji.get(task.priority, "⚪")
                due_str = ""
                if task.due_date:
                    due_str = f" (due: {task.due_date.strftime('%Y-%m-%d')})"
                message += f"  {i}. {priority_icon} {task.title}{due_str}\n"
            message += "\n"
        
        return message
    
    elif group_by == "due_date":
        # Group by due date
        now = datetime.utcnow()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        week_end = today + timedelta(days=7)
        
        overdue = []
        today_tasks = []
        tomorrow_tasks = []
        this_week = []
        upcoming = []
        no_due_date = []
        
        for task in tasks:
            if not task.due_date:
                no_due_date.append(task)
            elif task.due_date.date() < today:
                overdue.append(task)
            elif task.due_date.date() == today:
                today_tasks.append(task)
            elif task.due_date.date() == tomorrow:
                tomorrow_tasks.append(task)
            elif task.due_date.date() <= week_end:
                this_week.append(task)
            else:
                upcoming.append(task)
        
        message = "📋 **Your Tasks by Due Date:**\n\n"
        
        if overdue:
            message += f"⚠️ **OVERDUE** ({len(overdue)})\n"
            for i, task in enumerate(overdue, 1):
                priority_icon = priority_emoji.get(task.priority, "⚪")
                message += f"  {i}. {priority_icon} {task.title} (due: {task.due_date.strftime('%Y-%m-%d')})\n"
            message += "\n"
        
        if today_tasks:
            message += f"📅 **TODAY** ({len(today_tasks)})\n"
            for i, task in enumerate(today_tasks, 1):
                priority_icon = priority_emoji.get(task.priority, "⚪")
                message += f"  {i}. {priority_icon} {task.title}\n"
            message += "\n"
        
        if tomorrow_tasks:
            message += f"📅 **TOMORROW** ({len(tomorrow_tasks)})\n"
            for i, task in enumerate(tomorrow_tasks, 1):
                priority_icon = priority_emoji.get(task.priority, "⚪")
                message += f"  {i}. {priority_icon} {task.title}\n"
            message += "\n"
        
        if this_week:
            message += f"📅 **THIS WEEK** ({len(this_week)})\n"
            for i, task in enumerate(this_week, 1):
                priority_icon = priority_emoji.get(task.priority, "⚪")
                message += f"  {i}. {priority_icon} {task.title} (due: {task.due_date.strftime('%Y-%m-%d')})\n"
            message += "\n"
        
        if upcoming:
            message += f"📅 **UPCOMING** ({len(upcoming)})\n"
            for i, task in enumerate(upcoming, 1):
                priority_icon = priority_emoji.get(task.priority, "⚪")
                message += f"  {i}. {priority_icon} {task.title} (due: {task.due_date.strftime('%Y-%m-%d')})\n"
            message += "\n"
        
        if no_due_date:
            message += f"📋 **NO DUE DATE** ({len(no_due_date)})\n"
            for i, task in enumerate(no_due_date, 1):
                priority_icon = priority_emoji.get(task.priority, "⚪")
                message += f"  {i}. {priority_icon} {task.title}\n"
        
        return message
    
    else:
        # Default: simple list
        message = "📋 **Your Tasks:**\n\n"
        for i, task in enumerate(tasks, 1):
            priority_icon = priority_emoji.get(task.priority, "⚪")
            due_str = ""
            if task.due_date:
                due_str = f" (due: {task.due_date.strftime('%Y-%m-%d')})"
            message += f"{i}. {priority_icon} {task.title}{due_str}\n"
        return message


def format_task_detail(task: Task) -> str:
    """Format task detail view."""
    priority_emoji = {
        TaskPriority.URGENT: "🔴",
        TaskPriority.HIGH: "🔴",
        TaskPriority.MEDIUM: "🟡",
        TaskPriority.LOW: "🟢",
    }
    
    status_emoji = {
        TaskStatus.PENDING: "⏳",
        TaskStatus.IN_PROGRESS: "🔄",
        TaskStatus.COMPLETED: "✅",
        TaskStatus.OVERDUE: "⚠️",
    }
    
    message = f"📋 **Task Details:**\n\n"
    message += f"**{task.title}**\n\n"
    
    if task.description:
        message += f"📝 {task.description}\n\n"
    
    message += f"Status: {status_emoji.get(task.status, '⚪')} {task.status.value.capitalize()}\n"
    message += f"Priority: {priority_emoji.get(task.priority, '⚪')} {task.priority.value.capitalize()}\n"
    message += f"Category: {task.pillar.value.capitalize()}\n"
    
    if task.due_date:
        message += f"Due: {task.due_date.strftime('%Y-%m-%d %H:%M')}\n"
    else:
        message += "Due: No deadline\n"
    
    if task.estimated_duration:
        hours = task.estimated_duration // 60
        minutes = task.estimated_duration % 60
        if hours > 0:
            message += f"Est. Duration: {hours}h {minutes}m\n"
        else:
            message += f"Est. Duration: {minutes}m\n"
    
    if task.scheduled_start and task.scheduled_end:
        message += f"Scheduled: {task.scheduled_start.strftime('%Y-%m-%d %H:%M')} - {task.scheduled_end.strftime('%H:%M')}\n"
    
    return message


def get_task_list_keyboard(tasks: List[Task], page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
    """Get keyboard with task list items."""
    keyboard = []
    
    # Show tasks for current page
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_tasks = tasks[start_idx:end_idx]
    
    for task in page_tasks:
        # Truncate title if too long
        title = task.title[:40] + "..." if len(task.title) > 40 else task.title
        priority_icon = "🔴" if task.priority == TaskPriority.HIGH else "🟡" if task.priority == TaskPriority.MEDIUM else "🟢"
        keyboard.append([
            InlineKeyboardButton(
                f"{priority_icon} {title}",
                callback_data=f"task_view_{task.id}"
            )
        ])
    
    # Pagination
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"task_page_{page-1}"))
    if end_idx < len(tasks):
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"task_page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Action buttons
    keyboard.append([
        InlineKeyboardButton("➕ Add Task", callback_data="task_add"),
        InlineKeyboardButton("🔙 Back to Menu", callback_data="task_menu"),
    ])
    
    return InlineKeyboardMarkup(keyboard)


async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tasks command according to COMPREHENSIVE_PLAN.md."""
    user = update.effective_user
    
    async with AsyncSessionLocal() as session:
        # Get user
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await update.message.reply_text("Please start with /start first.")
            return
        
        # Check if user is onboarded
        if not db_user.is_onboarded:
            await update.message.reply_text(
                "Please complete onboarding first. Use /start to begin."
            )
            return
        
        # Get active tasks (pending and in_progress)
        active_tasks = await get_tasks(
            session,
            db_user.id,
            status=None,  # Get both pending and in_progress
            limit=50
        )
        
        # Filter to only active tasks
        active_tasks = [t for t in active_tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]]
        
        # Format and send tasks list
        if not active_tasks:
            await update.message.reply_text(
                "📋 You don't have any active tasks.\n\n"
                "Options:",
                reply_markup=get_tasks_menu_keyboard()
            )
            return
        
        # Format tasks grouped by priority
        tasks_text = format_task_list(active_tasks, group_by="priority")
        
        # Add options text
        tasks_text += "\nOptions:"
        
        await update.message.reply_text(
            tasks_text,
            parse_mode="Markdown",
            reply_markup=get_tasks_menu_keyboard()
        )


async def handle_task_creation_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle task creation flow messages."""
    user = update.effective_user
    text = update.message.text.strip()
    state = get_conversation_state(user.id)
    conv_context = get_conversation_context(user.id)
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await update.message.reply_text("Please start with /start first.")
            return
        
        if state == ConversationState.ADDING_TASK:
            # Handle task title input
            await handle_task_title_input(update, context, session, db_user, text)
        elif state == ConversationState.ADDING_TASK_PILLAR:
            # Handle pillar selection
            await handle_task_pillar_input(update, context, session, db_user, text)
        elif state == ConversationState.ADDING_TASK_PRIORITY:
            # Handle priority input
            await handle_task_priority_input(update, context, session, db_user, text)
        elif state == ConversationState.ADDING_TASK_DUE_DATE:
            # Handle due date input
            await handle_task_due_date_input(update, context, session, db_user, text)
        elif state == ConversationState.ADDING_TASK_DURATION:
            # Handle duration input
            await handle_task_duration_input(update, context, session, db_user, text)
        else:
            await update.message.reply_text("Please use the buttons to create a task.")


async def start_task_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command-based task creation flow."""
    user = update.effective_user
    
    set_conversation_state(user.id, ConversationState.ADDING_TASK)
    
    await update.message.reply_text(
        "📋 **Create New Task**\n\n"
        "What's the task title?\n\n"
        "Type the task name:"
    )


async def handle_task_title_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  session: AsyncSession, db_user: User, title: str) -> None:
    """Handle task title input with validation."""
    user = update.effective_user
    conv_context = get_conversation_context(user.id)
    
    # Validate title using validation helpers
    from edge_cases.validation import validate_task_title
    is_valid, error_msg = validate_task_title(title)
    
    if not is_valid:
        await update.message.reply_text(
            f"⚠️ {error_msg}\n\nPlease try again:"
        )
        return
    
    # Store validated title in context
    conv_context.data["task_title"] = title.strip()
    
    # Move to pillar selection
    set_conversation_state(user.id, ConversationState.ADDING_TASK_PILLAR)
    
    # Get user's available pillars (predefined + custom from onboarding)
    # For now, show predefined pillars
    from telegram_bot.keyboards import get_pillar_keyboard
    
    await update.message.reply_text(
        f"✅ Task title: **{title.strip()}**\n\n"
        "Select the category (pillar) for this task:",
        parse_mode="Markdown",
        reply_markup=get_pillar_keyboard()
    )


async def handle_task_pillar_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   session: AsyncSession, db_user: User, text: str) -> None:
    """Handle pillar selection input (called from callback)."""
    # This is handled by callback handler
    pass


async def handle_task_priority_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     session: AsyncSession, db_user: User, text: str) -> None:
    """Handle priority input."""
    # This is handled by callback handler
    pass


async def handle_task_due_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     session: AsyncSession, db_user: User, text: str) -> None:
    """Handle due date input with natural language parsing."""
    user = update.effective_user
    conv_context = get_conversation_context(user.id)
    
    # Parse date from natural language using dateutil
    text_lower = text.lower().strip()
    
    if text_lower == "none" or text_lower == "no" or text_lower == "n/a" or text_lower == "":
        conv_context.data["task_due_date"] = None
        # Move to duration
        set_conversation_state(user.id, ConversationState.ADDING_TASK_DURATION)
        await update.message.reply_text(
            "✅ No due date set.\n\n"
            "Estimated duration? (e.g., 2 hours, 30 minutes, or 'none'):"
        )
        return
    
    # Validate and parse due date using validation helpers
    from edge_cases.validation import validate_due_date
    is_valid, error_msg, parsed_date = validate_due_date(text, allow_past=False)
    
    if not is_valid:
        await update.message.reply_text(
            f"⚠️ {error_msg}\n\nPlease try again (e.g., 'tomorrow', 'Dec 25', 'next week', or 'none'):"
        )
        return
    
    if parsed_date:
        conv_context.data["task_due_date"] = parsed_date
        
        # Move to duration
        set_conversation_state(user.id, ConversationState.ADDING_TASK_DURATION)
        await update.message.reply_text(
            f"✅ Due date set: {parsed_date.strftime('%Y-%m-%d %H:%M')}\n\n"
            "Estimated duration? (e.g., 2 hours, 30 minutes, or 'none'):"
        )
    else:
        # No due date
        conv_context.data["task_due_date"] = None
        set_conversation_state(user.id, ConversationState.ADDING_TASK_DURATION)
        await update.message.reply_text(
            "✅ No due date set.\n\n"
            "Estimated duration? (e.g., 2 hours, 30 minutes, or 'none'):"
        )


async def handle_task_duration_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     session: AsyncSession, db_user: User, text: str) -> None:
    """Handle duration input with validation."""
    user = update.effective_user
    conv_context = get_conversation_context(user.id)
    
    text_lower = text.lower().strip()
    
    if text_lower == "none" or text_lower == "no" or text_lower == "n/a":
        conv_context.data["task_duration"] = None
    else:
        # Validate and parse duration using validation helpers
        from edge_cases.validation import validate_duration
        is_valid, error_msg, duration_minutes = validate_duration(text)
        
        if not is_valid:
            await update.message.reply_text(
                f"⚠️ {error_msg}\n\nPlease try again (e.g., '2 hours', '30 minutes', or 'none'):"
            )
            return
        
        conv_context.data["task_duration"] = duration_minutes
    
    # Show summary and ask for confirmation
    await show_task_summary(update, context, session, db_user)


async def parse_duration(text: str) -> Optional[int]:
    """Parse duration from natural language (returns minutes)."""
    import re
    
    text = text.lower().strip()
    
    # Pattern: "2 hours" or "2h"
    hour_pattern = r'(\d+)\s*(?:hours?|h)'
    hour_match = re.search(hour_pattern, text)
    hours = int(hour_match.group(1)) if hour_match else 0
    
    # Pattern: "30 minutes" or "30m"
    min_pattern = r'(\d+)\s*(?:minutes?|mins?|m)'
    min_match = re.search(min_pattern, text)
    minutes = int(min_match.group(1)) if min_match else 0
    
    # Pattern: "1.5 hours" or "1.5h"
    decimal_hour_pattern = r'(\d+\.\d+)\s*(?:hours?|h)'
    decimal_match = re.search(decimal_hour_pattern, text)
    if decimal_match:
        hours = int(float(decimal_match.group(1)))
        minutes = int((float(decimal_match.group(1)) - hours) * 60)
    
    total_minutes = hours * 60 + minutes
    
    return total_minutes if total_minutes > 0 else None


async def show_task_summary(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            session: AsyncSession, db_user: User) -> None:
    """Show task creation summary and ask for confirmation."""
    user = update.effective_user
    conv_context = get_conversation_context(user.id)
    
    title = conv_context.data.get("task_title", "")
    pillar = conv_context.data.get("task_pillar", "other")
    priority = conv_context.data.get("task_priority", "medium")
    due_date = conv_context.data.get("task_due_date")
    duration = conv_context.data.get("task_duration")
    
    summary = f"📋 **Task Summary:**\n\n"
    summary += f"**Title:** {title}\n"
    summary += f"**Category:** {pillar.capitalize()}\n"
    summary += f"**Priority:** {priority.capitalize()}\n"
    summary += f"**Due Date:** {due_date.strftime('%Y-%m-%d %H:%M') if due_date else 'No deadline'}\n"
    
    if duration:
        hours = duration // 60
        minutes = duration % 60
        if hours > 0:
            summary += f"**Duration:** {hours}h {minutes}m\n"
        else:
            summary += f"**Duration:** {minutes}m\n"
    else:
        summary += "**Duration:** Not specified\n"
    
    summary += "\nIs this correct?"
    
    from telegram_bot.keyboards import get_confirmation_keyboard
    
    await update.message.reply_text(
        summary,
        parse_mode="Markdown",
        reply_markup=get_confirmation_keyboard()
    )
    
    # Wait for confirmation in callback handler (task_callbacks.py)
