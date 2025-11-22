"""
Enable automatic flows based on detected patterns.
According to COMPREHENSIVE_PLAN.md Section 9: Adaptive Learning & Self-Improvement
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Habit, Task, User
from tasks.service import create_task
from memory.adaptive_learning import detect_recurring_patterns

logger = logging.getLogger(__name__)


async def enable_recurring_task_flow(
    session: AsyncSession,
    user_id: int,
    pattern: Dict[str, Any],
    flow_suggestion: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enable a recurring task flow based on detected pattern.
    
    This creates a habit record that tracks the pattern and can trigger
    automatic task creation reminders.
    
    Args:
        session: Database session
        user_id: User ID
        pattern: Detected recurring pattern
        flow_suggestion: Flow suggestion from suggest_automatic_flow()
    
    Returns:
        Dictionary with enabled flow details
    """
    try:
        # Check if flow already enabled (query by pattern_type, then filter by pattern_key in Python)
        pattern_key = pattern.get("pattern", "")
        existing = await session.execute(
            select(Habit).where(
                Habit.user_id == user_id,
                Habit.pattern_type == "enabled_recurring_flow"
            )
        )
        existing_habits = existing.scalars().all()
        
        # Find habit with matching pattern_key
        existing_habit = None
        for habit in existing_habits:
            if habit.pattern_data and habit.pattern_data.get("pattern_key") == pattern_key:
                existing_habit = habit
                break
        
        if existing_habit:
            # Update existing habit
            existing_habit.pattern_data = {
                "pattern_key": pattern.get("pattern", ""),
                "frequency_days": pattern.get("frequency_days", 0),
                "flow_type": flow_suggestion.get("flow_type"),
                "enabled_at": datetime.utcnow().isoformat(),
                "next_reminder": flow_suggestion.get("next_reminder").isoformat() if flow_suggestion.get("next_reminder") else None,
                "sample_tasks": pattern.get("sample_tasks", [])
            }
            existing_habit.confidence_score = pattern.get("confidence", 0.7)
            existing_habit.last_observed_at = datetime.utcnow()
        else:
            # Create new habit for enabled flow
            habit = Habit(
                user_id=user_id,
                pattern_type="enabled_recurring_flow",
                pattern_data={
                    "pattern_key": pattern.get("pattern", ""),
                    "frequency_days": pattern.get("frequency_days", 0),
                    "flow_type": flow_suggestion.get("flow_type"),
                    "enabled_at": datetime.utcnow().isoformat(),
                    "next_reminder": flow_suggestion.get("next_reminder").isoformat() if flow_suggestion.get("next_reminder") else None,
                    "sample_tasks": pattern.get("sample_tasks", [])
                },
                confidence_score=pattern.get("confidence", 0.7),
                last_observed_at=datetime.utcnow()
            )
            session.add(habit)
            existing_habit = habit
        
        await session.flush()
        
        result = {
            "success": True,
            "habit_id": existing_habit.id,
            "next_reminder": flow_suggestion.get("next_reminder"),
            "frequency_days": pattern.get("frequency_days", 0)
        }
        
        logger.info(f"Enabled recurring task flow for user {user_id}: {pattern.get('pattern')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error enabling recurring task flow: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def check_enabled_flows_for_reminders(
    session: AsyncSession,
    user_id: int
) -> list[Dict[str, Any]]:
    """
    Check enabled flows and determine if reminders should be sent.
    
    Args:
        session: Database session
        user_id: User ID
    
    Returns:
        List of flows that need reminders
    """
    try:
        # Get enabled recurring flows
        stmt = select(Habit).where(
            Habit.user_id == user_id,
            Habit.pattern_type == "enabled_recurring_flow"
        )
        result = await session.execute(stmt)
        enabled_flows = result.scalars().all()
        
        reminders_needed = []
        now = datetime.utcnow()
        
        for habit in enabled_flows:
            pattern_data = habit.pattern_data or {}
            next_reminder_str = pattern_data.get("next_reminder")
            
            if not next_reminder_str:
                # Calculate next reminder from frequency
                frequency_days = pattern_data.get("frequency_days", 0)
                if frequency_days > 0:
                    next_reminder = now + timedelta(days=frequency_days)
                else:
                    continue
            else:
                try:
                    next_reminder = datetime.fromisoformat(next_reminder_str)
                except (ValueError, TypeError):
                    continue
            
            # Check if reminder is due (within next 24 hours)
            time_until_reminder = (next_reminder - now).total_seconds() / 3600
            
            if 0 <= time_until_reminder <= 24:
                reminders_needed.append({
                    "habit_id": habit.id,
                    "pattern_data": pattern_data,
                    "next_reminder": next_reminder,
                    "time_until_hours": time_until_reminder,
                    "pattern_key": pattern_data.get("pattern_key", "")
                })
        
        return reminders_needed
        
    except Exception as e:
        logger.error(f"Error checking enabled flows for reminders: {e}")
        return []


async def send_recurring_task_reminder(
    session: AsyncSession,
    user_id: int,
    reminder_info: Dict[str, Any],
    application
) -> bool:
    """
    Send reminder for a recurring task pattern.
    
    Args:
        session: Database session
        user_id: User ID
        reminder_info: Reminder information from check_enabled_flows_for_reminders()
        application: Telegram application instance
    
    Returns:
        True if reminder sent successfully, False otherwise
    """
    try:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        pattern_data = reminder_info["pattern_data"]
        pattern_key = pattern_data.get("pattern_key", "")
        sample_tasks = pattern_data.get("sample_tasks", [])
        frequency_days = pattern_data.get("frequency_days", 0)
        
        # Build reminder message
        task_title = sample_tasks[0] if sample_tasks else pattern_key
        
        message = "🔄 **Recurring Task Reminder**\n\n"
        message += f"Based on your patterns, it's time to create:\n\n"
        message += f"**{task_title}**\n\n"
        message += f"I noticed you create this task every {frequency_days:.0f} days.\n\n"
        message += "Would you like me to create this task now?"
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Create Task", callback_data=f"create_recurring_task_{reminder_info['habit_id']}"),
            InlineKeyboardButton("⏰ Remind Later", callback_data=f"remind_later_{reminder_info['habit_id']}")
        ]])
        
        await application.bot.send_message(
            chat_id=user.telegram_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        # Update next reminder time
        habit = await session.get(Habit, reminder_info["habit_id"])
        if habit and habit.pattern_data:
            frequency_days = habit.pattern_data.get("frequency_days", 0)
            next_reminder = datetime.utcnow() + timedelta(days=frequency_days)
            habit.pattern_data["next_reminder"] = next_reminder.isoformat()
            habit.pattern_data["last_reminder_sent"] = datetime.utcnow().isoformat()
            await session.flush()
        
        logger.info(f"Sent recurring task reminder for user {user_id}: {pattern_key}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending recurring task reminder: {e}")
        return False


async def create_recurring_task_from_flow(
    session: AsyncSession,
    user_id: int,
    habit_id: int
) -> Optional[Task]:
    """
    Create a task based on an enabled recurring flow.
    
    Args:
        session: Database session
        user_id: User ID
        habit_id: Habit ID for the enabled flow
    
    Returns:
        Created Task object or None if error
    """
    try:
        habit = await session.get(Habit, habit_id)
        if not habit or habit.user_id != user_id:
            return None
        
        pattern_data = habit.pattern_data or {}
        sample_tasks = pattern_data.get("sample_tasks", [])
        pattern_key = pattern_data.get("pattern_key", "")
        
        # Use first sample task as title, or pattern key
        task_title = sample_tasks[0] if sample_tasks else pattern_key
        
        # Create task with default values
        task = await create_task(
            session,
            user_id,
            title=task_title,
            description=f"Auto-created from recurring pattern: {pattern_key}",
            pillar="other",  # Default - user can change
            priority="medium",
            due_date=None,  # No due date - user can set if needed
            estimated_duration=None
        )
        
        # Update habit to track creation
        if habit.pattern_data:
            if "instances_created" not in habit.pattern_data:
                habit.pattern_data["instances_created"] = 0
            habit.pattern_data["instances_created"] += 1
            habit.pattern_data["last_created_at"] = datetime.utcnow().isoformat()
            await session.flush()
        
        logger.info(f"Created recurring task for user {user_id} from flow {habit_id}: {task.title}")
        
        return task
        
    except Exception as e:
        logger.error(f"Error creating recurring task from flow: {e}")
        return None

