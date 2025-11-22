"""
Callback handlers for task management according to COMPREHENSIVE_PLAN.md
"""
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.models import User, Task, TaskStatus, TaskPriority, PillarType
from sqlalchemy import select
from telegram_bot.conversation import (
    ConversationState,
    get_conversation_state,
    get_conversation_context,
    set_conversation_state,
    clear_conversation_context,
)
from telegram_bot.handlers.tasks import (
    format_task_list,
    format_task_detail,
    get_tasks_menu_keyboard,
    get_filter_keyboard,
    get_pillar_filter_keyboard,
    get_priority_filter_keyboard,
    get_status_filter_keyboard,
    get_due_date_filter_keyboard,
    get_sort_keyboard,
    get_task_list_keyboard,
    start_task_creation,
)
from tasks.service import (
    create_task,
    get_tasks,
    get_task,
    update_task,
    delete_task,
    complete_task,
)
from telegram_bot.keyboards import get_task_actions_keyboard, get_confirmation_keyboard, get_pillar_keyboard, get_priority_keyboard

logger = logging.getLogger(__name__)


async def handle_task_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route task management callbacks."""
    query = update.callback_query
    callback_data = query.data
    user = update.effective_user
    
    # Acknowledge callback immediately
    await query.answer()
    
    logger.info(f"Task callback: {callback_data} from user {user.id}")
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await query.message.reply_text("Please start with /start first.")
            return
        
        # Route based on callback type
        if callback_data == "task_add":
            await handle_task_add_callback(update, context, session, db_user)
        elif callback_data == "task_view_all":
            await handle_task_view_all(update, context, session, db_user)
        elif callback_data == "task_menu":
            await handle_task_menu(update, context, session, db_user)
        elif callback_data == "task_filter_menu":
            await handle_task_filter_menu(update, context, session, db_user)
        elif callback_data == "task_sort_menu":
            await handle_task_sort_menu(update, context, session, db_user)
        elif callback_data.startswith("task_view_"):
            task_id = int(callback_data.replace("task_view_", ""))
            await handle_task_view_detail(update, context, session, db_user, task_id)
        elif callback_data.startswith("task_complete_"):
            task_id = int(callback_data.replace("task_complete_", ""))
            await handle_task_complete(update, context, session, db_user, task_id)
        elif callback_data.startswith("task_edit_"):
            task_id = int(callback_data.replace("task_edit_", ""))
            await handle_task_edit(update, context, session, db_user, task_id)
        elif callback_data.startswith("task_delete_"):
            task_id = int(callback_data.replace("task_delete_", ""))
            await handle_task_delete(update, context, session, db_user, task_id)
        elif callback_data.startswith("task_schedule_confirm_"):
            # Format: task_schedule_confirm_{task_id}_{start_timestamp}_{end_timestamp}
            parts = callback_data.replace("task_schedule_confirm_", "").split("_")
            task_id = int(parts[0])
            start_timestamp = int(parts[1])
            end_timestamp = int(parts[2])
            await handle_task_schedule_confirm(update, context, session, db_user, task_id, start_timestamp, end_timestamp)
        elif callback_data.startswith("task_unschedule_confirm_"):
            task_id = int(callback_data.replace("task_unschedule_confirm_", ""))
            await handle_task_unschedule_confirm(update, context, session, db_user, task_id)
        elif callback_data.startswith("task_unschedule_"):
            task_id = int(callback_data.replace("task_unschedule_", ""))
            await handle_task_unschedule(update, context, session, db_user, task_id)
        elif callback_data.startswith("task_schedule_confirm_final_"):
            # Format: task_schedule_confirm_final_{task_id}_{start_timestamp}_{end_timestamp}
            parts = callback_data.replace("task_schedule_confirm_final_", "").split("_")
            task_id = int(parts[0])
            start_timestamp = int(parts[1])
            end_timestamp = int(parts[2])
            start_time = datetime.fromtimestamp(start_timestamp)
            end_time = datetime.fromtimestamp(end_timestamp)
            await _do_schedule_task(session, query, task_id, start_time, end_time, db_user.id)
        elif callback_data.startswith("task_reschedule_"):
            task_id = int(callback_data.replace("task_reschedule_", ""))
            await handle_task_reschedule(update, context, session, db_user, task_id)
        elif callback_data.startswith("task_schedule_manual_"):
            task_id = int(callback_data.replace("task_schedule_manual_", ""))
            await handle_task_schedule_manual(update, context, session, db_user, task_id)
        elif callback_data.startswith("task_schedule_"):
            task_id = int(callback_data.replace("task_schedule_", ""))
            await handle_task_schedule(update, context, session, db_user, task_id)
        elif callback_data.startswith("filter_"):
            await handle_task_filter(update, context, session, db_user, callback_data)
        elif callback_data.startswith("sort_"):
            await handle_task_sort(update, context, session, db_user, callback_data)
        elif callback_data == "confirm" or callback_data == "cancel":
            await handle_task_confirmation(update, context, session, db_user, callback_data)
        elif callback_data.startswith("pillar_"):
            # Handle pillar selection during task creation
            await handle_task_pillar_callback(update, context, session, db_user, callback_data)
        elif callback_data.startswith("priority_"):
            # Handle priority selection during task creation
            await handle_task_priority_callback(update, context, session, db_user, callback_data)
        else:
            await query.message.edit_text(f"Unknown callback: {callback_data}")


async def handle_task_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   session, db_user: User) -> None:
    """Handle 'Add Task' button click."""
    query = update.callback_query
    user = update.effective_user
    
    # Clear any existing task creation context
    clear_conversation_context(user.id)
    
    # Start task creation flow
    set_conversation_state(user.id, ConversationState.ADDING_TASK)
    
    await query.message.edit_text(
        "📋 **Create New Task**\n\n"
        "What's the task title?\n\n"
        "Type the task name:"
    )


async def handle_task_view_all(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               session, db_user: User) -> None:
    """Handle 'View All Tasks' button."""
    query = update.callback_query
    
    tasks = await get_tasks(session, db_user.id, limit=50)
    
    if not tasks:
        await query.message.edit_text(
            "📋 You don't have any tasks.\n\n"
            "Use 'Add Task' to create a new task!",
            reply_markup=get_tasks_menu_keyboard()
        )
        return
    
    # Format tasks list
    tasks_text = format_task_list(tasks, group_by="priority")
    tasks_text += "\nClick on a task to view details:"
    
    await query.message.edit_text(
        tasks_text,
        parse_mode="Markdown",
        reply_markup=get_task_list_keyboard(tasks, page=0)
    )


async def handle_task_menu(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          session, db_user: User) -> None:
    """Handle 'Back to Menu' button."""
    query = update.callback_query
    
    # Get active tasks count
    active_tasks = await get_tasks(
        session,
        db_user.id,
        status=None,
        limit=50
    )
    active_tasks = [t for t in active_tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]]
    
    message = f"📋 **Task Management**\n\n"
    message += f"You have {len(active_tasks)} active task(s).\n\n"
    message += "Options:"
    
    await query.message.edit_text(
        message,
        parse_mode="Markdown",
        reply_markup=get_tasks_menu_keyboard()
    )


async def handle_task_view_detail(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  session, db_user: User, task_id: int) -> None:
    """Handle task detail view."""
    query = update.callback_query
    
    task = await get_task(session, task_id, db_user.id)
    
    if not task:
        await query.answer("Task not found", show_alert=True)
        return
    
    # Format task detail
    detail_text = format_task_detail(task)
    detail_text += "\n\nOptions:"
    
    await query.message.edit_text(
        detail_text,
        parse_mode="Markdown",
        reply_markup=get_task_actions_keyboard(task_id)
    )


async def handle_task_complete(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               session, db_user: User, task_id: int) -> None:
    """Handle task completion."""
    query = update.callback_query
    
    task = await complete_task(session, task_id, db_user.id)
    
    if not task:
        await query.answer("Task not found", show_alert=True)
        return
    
    await session.commit()
    
    await query.answer("✅ Task completed!")
    
    # Ask for actual duration
    await query.message.reply_text(
        "✅ Task completed! Great job! 🎉\n\n"
        "How long did it actually take? (e.g., 1.5 hours, 30 minutes)\n\n"
        "Or type 'skip' to skip this:",
        reply_markup=None
    )
    
    # Store task_id in context for duration collection
    conv_context = get_conversation_context(query.from_user.id)
    conv_context.data["completing_task_id"] = task_id
    
    # Update task list view
    active_tasks = await get_tasks(
        session,
        db_user.id,
        status=None,
        limit=50
    )
    active_tasks = [t for t in active_tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]]
    
    if active_tasks:
        tasks_text = format_task_list(active_tasks, group_by="priority")
        await query.message.reply_text(
            tasks_text,
            parse_mode="Markdown",
            reply_markup=get_tasks_menu_keyboard()
        )


async def handle_task_edit(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          session, db_user: User, task_id: int) -> None:
    """Handle task edit request."""
    query = update.callback_query
    
    task = await get_task(session, task_id, db_user.id)
    
    if not task:
        await query.answer("Task not found", show_alert=True)
        return
    
    # TODO: Implement task editing flow
    await query.message.edit_text(
        "✏️ **Edit Task**\n\n"
        "Task editing functionality coming soon!\n\n"
        f"Task: {task.title}",
        reply_markup=get_task_actions_keyboard(task_id)
    )


async def handle_task_delete(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            session, db_user: User, task_id: int) -> None:
    """Handle task delete request."""
    query = update.callback_query
    
    task = await get_task(session, task_id, db_user.id)
    
    if not task:
        await query.answer("Task not found", show_alert=True)
        return
    
    # Show confirmation
    await query.message.edit_text(
        f"⚠️ **Are you sure you want to delete this task?**\n\n"
        f"**Task:** {task.title}\n\n"
        "This action cannot be undone.",
        parse_mode="Markdown",
        reply_markup=get_confirmation_keyboard()
    )
    
    # Store task_id in context for confirmation
    conv_context = get_conversation_context(query.from_user.id)
    conv_context.data["deleting_task_id"] = task_id


async def handle_task_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               session, db_user: User, task_id: int) -> None:
    """Handle task scheduling request with time slot suggestions."""
    query = update.callback_query
    
    from tasks.service import get_task
    task = await get_task(session, task_id, db_user.id)
    
    if not task:
        await query.answer("Task not found", show_alert=True)
        return
    
    # Check if user is connected to Google Calendar
    if not db_user.google_calendar_connected:
        await query.answer("Google Calendar not connected", show_alert=True)
        await query.message.edit_text(
            "📅 **Schedule Task**\n\n"
            f"**Task:** {task.title}\n\n"
            "❌ Google Calendar is not connected.\n\n"
            "Please connect your Google Calendar first using `/calendar` to schedule tasks.",
            parse_mode="Markdown"
        )
        return
    
    # Check if task is already scheduled
    if task.calendar_event_id:
        await query.answer("Task already scheduled", show_alert=True)
        scheduled_time = task.scheduled_start.strftime('%Y-%m-%d %H:%M') if task.scheduled_start else "Unknown"
        await query.message.edit_text(
            "📅 **Task Already Scheduled**\n\n"
            f"**Task:** {task.title}\n\n"
            f"**Scheduled:** {scheduled_time}\n\n"
            "Would you like to reschedule?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Reschedule", callback_data=f"task_reschedule_{task_id}"),
                InlineKeyboardButton("❌ Unschedule", callback_data=f"task_unschedule_{task_id}")
            ], [
                InlineKeyboardButton("🔙 Back", callback_data=f"task_detail_{task_id}")
            ]])
        )
        return
    
    # Get time slot suggestions
    from tasks.scheduling import suggest_time_slots
    
    duration = task.estimated_duration or 60  # Default 1 hour
    suggestions = await suggest_time_slots(
        session,
        db_user.id,
        duration,
        preferred_date=None  # Suggest starting from today
    )
    
    if not suggestions:
        await query.message.edit_text(
            "📅 **Schedule Task**\n\n"
            f"**Task:** {task.title}\n\n"
            "⚠️ No available time slots found in the next 3 days.\n\n"
            "Please try scheduling manually or adjust your calendar.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✏️ Schedule Manually", callback_data=f"task_schedule_manual_{task_id}"),
                InlineKeyboardButton("🔙 Back", callback_data=f"task_detail_{task_id}")
            ]])
        )
        return
    
    # Format suggestions message
    message = f"📅 **Schedule Task**\n\n**Task:** {task.title}\n"
    if task.estimated_duration:
        message += f"**Duration:** {task.estimated_duration} minutes\n"
    message += "\n**Suggested Time Slots:**\n\n"
    
    # Create keyboard with suggestions
    keyboard = []
    
    for i, suggestion in enumerate(suggestions[:5], 1):
        start_time = suggestion['start_time']
        end_time = suggestion['end_time']
        
        time_str = start_time.strftime('%a %b %d, %I:%M %p')
        quality_emoji = "⭐" if suggestion['quality_score'] > 0.8 else "📌"
        
        message += f"{i}. {quality_emoji} {time_str}\n"
        
        # Create callback data with timestamp
        callback_data = f"task_schedule_confirm_{task_id}_{int(start_time.timestamp())}_{int(end_time.timestamp())}"
        keyboard.append([InlineKeyboardButton(
            f"{i}. {time_str}",
            callback_data=callback_data
        )])
    
    keyboard.append([
        InlineKeyboardButton("✏️ Schedule Manually", callback_data=f"task_schedule_manual_{task_id}"),
        InlineKeyboardButton("🔙 Back", callback_data=f"task_detail_{task_id}")
    ])
    
    await query.message.edit_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_task_schedule_confirm(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session,
    db_user: User,
    task_id: int,
    start_timestamp: int,
    end_timestamp: int
) -> None:
    """Handle scheduling confirmation with selected time slot."""
    query = update.callback_query
    
    from tasks.service import get_task
    task = await get_task(session, task_id, db_user.id)
    
    if not task:
        await query.answer("Task not found", show_alert=True)
        return
    
    # Convert timestamps to datetime
    start_time = datetime.fromtimestamp(start_timestamp)
    end_time = datetime.fromtimestamp(end_timestamp)
    
    # Check guardrails - scheduling requires confirmation
    from edge_cases.guardrails import check_user_autonomy
    autonomy_check = await check_user_autonomy("schedule_task", requires_confirmation=True)
    
    if autonomy_check["requires_confirmation"]:
        # Show confirmation dialog
        time_str = start_time.strftime('%Y-%m-%d %I:%M %p')
        await query.message.edit_text(
            "📅 **Confirm Scheduling**\n\n"
            f"**Task:** {task.title}\n\n"
            f"**Time:** {time_str}\n"
            f"**Duration:** {(end_time - start_time).total_seconds() / 60:.0f} minutes\n\n"
            "Schedule this task to your calendar?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Confirm", callback_data=f"task_schedule_confirm_final_{task_id}_{start_timestamp}_{end_timestamp}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"task_detail_{task_id}")
            ]])
        )
        
        # Store scheduling info in context for final confirmation
        conv_context = get_conversation_context(query.from_user.id)
        conv_context.data["scheduling_task_id"] = task_id
        conv_context.data["scheduling_start"] = start_timestamp
        conv_context.data["scheduling_end"] = end_timestamp
        return
    
    # Direct scheduling without confirmation
    await _do_schedule_task(session, query, task_id, start_time, end_time, db_user.id)


async def _do_schedule_task(
    session,
    query,
    task_id: int,
    start_time: datetime,
    end_time: datetime,
    user_id: int
) -> None:
    """Actually schedule the task to calendar."""
    from tasks.scheduling import schedule_task_to_calendar
    
    success, event_id, error_msg = await schedule_task_to_calendar(
        session,
        user_id,
        task_id,
        start_time,
        end_time
    )
    
    if not success:
        await query.answer(f"❌ {error_msg}", show_alert=True)
        await query.message.edit_text(
            f"⚠️ **Scheduling Failed**\n\n{error_msg}\n\n"
            "Please try again with a different time slot.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data=f"task_detail_{task_id}")
            ]])
        )
        return
    
    await session.commit()
    
    await query.answer("✅ Task scheduled!")
    time_str = start_time.strftime('%Y-%m-%d %I:%M %p')
    await query.message.edit_text(
        f"✅ **Task Scheduled!**\n\n"
        f"**Task:** {task.title}\n\n"
        f"**Time:** {time_str}\n\n"
        "The task has been added to your Google Calendar.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Task", callback_data=f"task_detail_{task_id}")
        ]])
    )
    
    logger.info(f"Task {task_id} scheduled to calendar at {time_str}")


async def handle_task_unschedule(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session,
    db_user: User,
    task_id: int
) -> None:
    """Handle unscheduling a task from calendar."""
    query = update.callback_query
    
    from tasks.service import get_task
    task = await get_task(session, task_id, db_user.id)
    
    if not task:
        await query.answer("Task not found", show_alert=True)
        return
    
    if not task.calendar_event_id:
        await query.answer("Task is not scheduled", show_alert=True)
        return
    
    # Show confirmation (guardrails)
    await query.message.edit_text(
        "⚠️ **Unschedule Task?**\n\n"
        f"**Task:** {task.title}\n\n"
        "Remove this task from your calendar?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Confirm", callback_data=f"task_unschedule_confirm_{task_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"task_detail_{task_id}")
        ]])
    )


async def handle_task_reschedule(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session,
    db_user: User,
    task_id: int
) -> None:
    """Handle rescheduling a task (show new time slot suggestions)."""
    # Same as handle_task_schedule but show different message
    query = update.callback_query
    
    from tasks.service import get_task
    task = await get_task(session, task_id, db_user.id)
    
    if not task:
        await query.answer("Task not found", show_alert=True)
        return
    
    # Get time slot suggestions (same as scheduling)
    from tasks.scheduling import suggest_time_slots
    
    duration = task.estimated_duration or 60
    suggestions = await suggest_time_slots(
        session,
        db_user.id,
        duration,
        preferred_date=None
    )
    
    if not suggestions:
        await query.message.edit_text(
            "📅 **Reschedule Task**\n\n"
            f"**Task:** {task.title}\n\n"
            "⚠️ No available time slots found in the next 3 days.\n\n"
            "Please try scheduling manually or adjust your calendar.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✏️ Schedule Manually", callback_data=f"task_schedule_manual_{task_id}"),
                InlineKeyboardButton("🔙 Back", callback_data=f"task_detail_{task_id}")
            ]])
        )
        return
    
    # Format suggestions message
    message = f"📅 **Reschedule Task**\n\n**Task:** {task.title}\n"
    if task.estimated_duration:
        message += f"**Duration:** {task.estimated_duration} minutes\n"
    message += "\n**Suggested Time Slots:**\n\n"
    
    keyboard = []
    for i, suggestion in enumerate(suggestions[:5], 1):
        start_time = suggestion['start_time']
        end_time = suggestion['end_time']
        time_str = start_time.strftime('%a %b %d, %I:%M %p')
        quality_emoji = "⭐" if suggestion['quality_score'] > 0.8 else "📌"
        
        message += f"{i}. {quality_emoji} {time_str}\n"
        
        callback_data = f"task_schedule_confirm_{task_id}_{int(start_time.timestamp())}_{int(end_time.timestamp())}"
        keyboard.append([InlineKeyboardButton(
            f"{i}. {time_str}",
            callback_data=callback_data
        )])
    
    keyboard.append([
        InlineKeyboardButton("✏️ Schedule Manually", callback_data=f"task_schedule_manual_{task_id}"),
        InlineKeyboardButton("🔙 Back", callback_data=f"task_detail_{task_id}")
    ])
    
    await query.message.edit_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_task_schedule_manual(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session,
    db_user: User,
    task_id: int
) -> None:
    """Handle manual scheduling request (prompt for time input)."""
    query = update.callback_query
    
    from tasks.service import get_task
    task = await get_task(session, task_id, db_user.id)
    
    if not task:
        await query.answer("Task not found", show_alert=True)
        return
    
    # Set conversation state for manual scheduling
    set_conversation_state(query.from_user.id, ConversationState.SCHEDULING_TASK)
    
    # Store task_id in context
    conv_context = get_conversation_context(query.from_user.id)
    conv_context.data["scheduling_task_id"] = task_id
    
    await query.message.edit_text(
        "📅 **Manual Scheduling**\n\n"
        f"**Task:** {task.title}\n\n"
        "Please provide the start time for this task.\n\n"
        "You can use natural language like:\n"
        "- 'tomorrow 2pm'\n"
        "- 'Dec 25, 10am'\n"
        "- 'next Monday 9am'\n"
        "- Or format: YYYY-MM-DD HH:MM",
        parse_mode="Markdown"
    )
    
    # Also send as new message for input
    await query.message.reply_text(
        "Type the start time for your task:"
    )




async def handle_task_unschedule_confirm(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session,
    db_user: User,
    task_id: int
) -> None:
    """Confirm and execute task unscheduling."""
    query = update.callback_query
    
    from tasks.scheduling import unschedule_task_from_calendar
    
    success, error_msg = await unschedule_task_from_calendar(
        session,
        db_user.id,
        task_id
    )
    
    if not success:
        await query.answer(f"❌ {error_msg}", show_alert=True)
        await query.message.edit_text(
            f"⚠️ **Unschedule Failed**\n\n{error_msg}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data=f"task_detail_{task_id}")
            ]])
        )
        return
    
    await session.commit()
    
    await query.answer("✅ Task unscheduled!")
    await query.message.edit_text(
        "✅ **Task Unscheduled**\n\n"
        "The task has been removed from your Google Calendar.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Task", callback_data=f"task_detail_{task_id}")
        ]])
    )
    
    logger.info(f"Task {task_id} unscheduled from calendar")


async def handle_task_filter_menu(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  session, db_user: User) -> None:
    """Show filter menu."""
    query = update.callback_query
    
    await query.message.edit_text(
        "🔍 **Filter Tasks**\n\n"
        "Select a filter option:",
        parse_mode="Markdown",
        reply_markup=get_filter_keyboard()
    )


async def handle_task_sort_menu(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                session, db_user: User) -> None:
    """Show sort menu."""
    query = update.callback_query
    
    await query.message.edit_text(
        "🔀 **Sort Tasks**\n\n"
        "Select a sort option:",
        parse_mode="Markdown",
        reply_markup=get_sort_keyboard()
    )


async def handle_task_filter(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            session, db_user: User, callback_data: str) -> None:
    """Handle filter selection."""
    query = update.callback_query
    
    if callback_data == "filter_priority":
        await query.message.edit_text(
            "🔍 **Filter by Priority**\n\n"
            "Select priority:",
            reply_markup=get_priority_filter_keyboard()
        )
    elif callback_data == "filter_pillar":
        await query.message.edit_text(
            "🔍 **Filter by Category**\n\n"
            "Select category:",
            reply_markup=get_pillar_filter_keyboard()
        )
    elif callback_data == "filter_status":
        await query.message.edit_text(
            "🔍 **Filter by Status**\n\n"
            "Select status:",
            reply_markup=get_status_filter_keyboard()
        )
    elif callback_data == "filter_due_date":
        await query.message.edit_text(
            "🔍 **Filter by Due Date**\n\n"
            "Select option:",
            reply_markup=get_due_date_filter_keyboard()
        )
    elif callback_data == "filter_clear":
        # Clear filters and show all tasks
        active_tasks = await get_tasks(session, db_user.id, limit=50)
        active_tasks = [t for t in active_tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]]
        
        tasks_text = format_task_list(active_tasks, group_by="priority")
        
        await query.message.edit_text(
            tasks_text,
            parse_mode="Markdown",
            reply_markup=get_tasks_menu_keyboard()
        )
    elif callback_data.startswith("filter_apply_"):
        # Apply filter (implementation coming)
        await query.answer("Filter applied!")
        await handle_task_menu(update, context, session, db_user)


async def handle_task_sort(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          session, db_user: User, callback_data: str) -> None:
    """Handle sort selection."""
    query = update.callback_query
    
    # Get tasks
    active_tasks = await get_tasks(session, db_user.id, limit=50)
    active_tasks = [t for t in active_tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]]
    
    # Apply sorting
    if callback_data == "sort_priority":
        active_tasks.sort(key=lambda t: (
            {"urgent": 0, "high": 1, "medium": 2, "low": 3}.get(t.priority.value, 4),
            t.due_date or datetime.max
        ))
        group_by = "priority"
    elif callback_data == "sort_due_date":
        active_tasks.sort(key=lambda t: t.due_date or datetime.max)
        group_by = "due_date"
    elif callback_data == "sort_created":
        active_tasks.sort(key=lambda t: t.created_at, reverse=True)
        group_by = "priority"  # Default grouping
    elif callback_data == "sort_pillar":
        active_tasks.sort(key=lambda t: t.pillar.value)
        group_by = "pillar"
    else:
        group_by = "priority"
    
    tasks_text = format_task_list(active_tasks, group_by=group_by)
    
    await query.message.edit_text(
        tasks_text,
        parse_mode="Markdown",
        reply_markup=get_tasks_menu_keyboard()
    )


async def handle_task_pillar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     session, db_user: User, callback_data: str) -> None:
    """Handle pillar selection during task creation - Track corrections for learning."""
    query = update.callback_query
    user = update.effective_user
    
    # Extract pillar from callback (format: "pillar_work")
    pillar_name = callback_data.replace("pillar_", "")
    
    conv_context = get_conversation_context(user.id)
    
    # Check if this is a correction (user changing AI suggestion)
    original_pillar = conv_context.data.get("original_suggested_pillar") or conv_context.data.get("task_pillar")
    if original_pillar and original_pillar != pillar_name:
        # Track correction for learning
        from memory.adaptive_learning import track_correction_and_learn
        
        await track_correction_and_learn(
            session,
            db_user.id,
            action="pillar",
            original_value=original_pillar,
            corrected_value=pillar_name,
            context={
                "task_description": conv_context.data.get("task_title", ""),
                "task_id": conv_context.data.get("task_id"),
                "nl_task_creation": conv_context.data.get("nl_task_creation", False)
            }
        )
        await session.commit()
    
    conv_context.data["task_pillar"] = pillar_name
    
    # Move to priority selection
    set_conversation_state(user.id, ConversationState.ADDING_TASK_PRIORITY)
    
    await query.message.edit_text(
        f"✅ Category: **{pillar_name.capitalize()}**\n\n"
        "What's the priority?",
        parse_mode="Markdown",
        reply_markup=get_priority_keyboard()
    )


async def handle_task_priority_callback(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                       session, db_user: User, callback_data: str) -> None:
    """Handle priority selection during task creation - Track corrections for learning."""
    query = update.callback_query
    user = update.effective_user
    
    # Extract priority from callback (format: "priority_high")
    priority_name = callback_data.replace("priority_", "")
    
    conv_context = get_conversation_context(user.id)
    
    # Check if this is a correction (user changing AI suggestion)
    original_priority = conv_context.data.get("original_suggested_priority") or conv_context.data.get("task_priority")
    if original_priority and original_priority != priority_name:
        # Track correction for learning
        from memory.adaptive_learning import track_correction_and_learn
        
        await track_correction_and_learn(
            session,
            db_user.id,
            action="priority",
            original_value=original_priority,
            corrected_value=priority_name,
            context={
                "task_description": conv_context.data.get("task_title", ""),
                "task_id": conv_context.data.get("task_id"),
                "pillar": conv_context.data.get("task_pillar")
            }
        )
        await session.commit()
    
    conv_context.data["task_priority"] = priority_name
    
    # Move to due date
    set_conversation_state(user.id, ConversationState.ADDING_TASK_DUE_DATE)
    
    await query.message.edit_text(
        f"✅ Priority: **{priority_name.capitalize()}**\n\n"
        "When is it due? (e.g., tomorrow, Dec 25, next week)\n\n"
        "Or type 'none' for no due date:"
    )


async def handle_task_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  session, db_user: User, callback_data: str) -> None:
    """Handle task creation/editing confirmation."""
    query = update.callback_query
    user = update.effective_user
    conv_context = get_conversation_context(user.id)
    
    if callback_data == "confirm":
        # Check if we're confirming task creation or deletion
        if "deleting_task_id" in conv_context.data:
            # Confirm deletion
            task_id = conv_context.data["deleting_task_id"]
            deleted = await delete_task(session, task_id, db_user.id)
            await session.commit()
            
            if deleted:
                await query.answer("✅ Task deleted!")
                await query.message.edit_text(
                    "🗑️ Task deleted.",
                    reply_markup=None
                )
                
                # Show updated task list
                from telegram_bot.handlers.tasks import tasks_command
                await tasks_command(update, context)
            else:
                await query.answer("❌ Task not found", show_alert=True)
            
            conv_context.data.pop("deleting_task_id", None)
            
        elif "task_title" in conv_context.data:
            # Confirm task creation with validation
            title = conv_context.data.get("task_title")
            pillar = conv_context.data.get("task_pillar", "other")
            priority = conv_context.data.get("task_priority", "medium")
            due_date = conv_context.data.get("task_due_date")
            duration = conv_context.data.get("task_duration")
            
            # Validate inputs before creating
            from edge_cases.validation import validate_task_title
            is_valid, error_msg = validate_task_title(title)
            
            if not is_valid:
                await query.answer("❌ Validation error", show_alert=True)
                await query.message.edit_text(
                    f"⚠️ **Validation Error**\n\n{error_msg}\n\n"
                    "Please restart task creation with /tasks",
                    parse_mode="Markdown"
                )
                clear_conversation_context(user.id)
                return
            
            # Create task with validation (create_task now validates internally)
            try:
                task = await create_task(
                    session,
                    db_user.id,
                    title=title,
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
                    parse_mode="Markdown",
                    reply_markup=None
                )
                
                # Clear task creation context
                clear_conversation_context(user.id)
                
                logger.info(f"User {user.id} created task {task.id}: {task.title}")
            except ValueError as e:
                # Validation error from create_task
                await query.answer("❌ Validation error", show_alert=True)
                await query.message.edit_text(
                    f"⚠️ **Validation Error**\n\n{str(e)}\n\n"
                    "Please restart task creation with /tasks",
                    parse_mode="Markdown"
                )
                clear_conversation_context(user.id)
    
    else:  # cancel
        await query.answer("❌ Cancelled")
        await query.message.edit_text(
            "❌ Cancelled.",
            reply_markup=None
        )
        
        # Clear context
        clear_conversation_context(user.id)

