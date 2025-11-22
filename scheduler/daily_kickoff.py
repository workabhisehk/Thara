"""
Enhanced Daily Kickoff Flow according to COMPREHENSIVE_PLAN.md Section 7
Includes free hours calculation and AI-powered task recommendations
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from database.connection import AsyncSessionLocal
from database.models import User, Task, TaskStatus, TaskPriority
from sqlalchemy import select
from google_calendar.client import list_events
from tasks.service import get_tasks
from tasks.ai_prioritization import ai_prioritize_tasks
from tasks.priority_queue import get_priority_queue
from telegram_bot.bot import create_application
from ai.langchain_setup import get_llm
from langchain_core.messages import HumanMessage
import pytz

logger = logging.getLogger(__name__)


def parse_calendar_datetime(date_str: str, timezone_str: str = "UTC") -> Optional[datetime]:
    """Parse datetime from Google Calendar event."""
    if not date_str:
        return None
    
    try:
        # Handle timezone
        tz = pytz.timezone(timezone_str) if timezone_str else pytz.UTC
        
        # Parse ISO format
        if 'T' in date_str:
            # Has time component
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # Convert to UTC
            if dt.tzinfo is None:
                dt = tz.localize(dt)
            dt = dt.astimezone(pytz.UTC)
            return dt.replace(tzinfo=None)  # Remove timezone for comparison
        else:
            # Date only (all-day event)
            dt = datetime.fromisoformat(date_str)
            dt = tz.localize(dt).replace(hour=23, minute=59)  # End of day
            dt = dt.astimezone(pytz.UTC)
            return dt.replace(tzinfo=None)
    except Exception as e:
        logger.warning(f"Could not parse datetime '{date_str}': {e}")
        return None


def calculate_free_hours(
    events: List[Dict[str, Any]],
    work_start_hour: int,
    work_end_hour: int,
    timezone_str: str = "UTC"
) -> List[Dict[str, Any]]:
    """
    Calculate free hours (available time slots) between calendar events.
    According to COMPREHENSIVE_PLAN.md Section 7.
    
    Returns list of free slots with:
    - time_range: "09:30 AM - 10:00 AM"
    - duration_minutes: 30
    - time_of_day: "morning" | "mid-morning" | "afternoon" | "evening"
    - energy_level: "high" | "medium" | "low"
    """
    now = datetime.utcnow()
    today = now.date()
    
    # Filter to today's events only
    today_events = []
    for event in events:
        start_dt = parse_calendar_datetime(event.get('start'), timezone_str)
        if start_dt and start_dt.date() == today:
            end_dt = parse_calendar_datetime(event.get('end'), timezone_str)
            if end_dt:
                today_events.append((start_dt, end_dt))
    
    # Sort events by start time
    today_events.sort(key=lambda x: x[0])
    
    # Build work day timeline
    work_start = now.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
    work_end = now.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)
    
    # Ensure work_start is not in the past
    if work_start < now:
        work_start = now.replace(minute=0, second=0, microsecond=0)
    
    free_slots = []
    
    # Slot from work_start to first event
    if today_events:
        first_event_start = today_events[0][0]
        if work_start < first_event_start:
            slot_duration = (first_event_start - work_start).total_seconds() / 60
            if slot_duration >= 15:  # Minimum 15 minutes
                free_slots.append({
                    "start": work_start,
                    "end": first_event_start,
                    "duration_minutes": int(slot_duration)
                })
        
        # Slots between consecutive events
        for i in range(len(today_events) - 1):
            current_end = today_events[i][1]
            next_start = today_events[i + 1][0]
            
            if current_end < next_start:
                slot_duration = (next_start - current_end).total_seconds() / 60
                if slot_duration >= 15:  # Minimum 15 minutes
                    free_slots.append({
                        "start": current_end,
                        "end": next_start,
                        "duration_minutes": int(slot_duration)
                    })
        
        # Slot from last event to work_end
        last_event_end = today_events[-1][1]
        if last_event_end < work_end:
            slot_duration = (work_end - last_event_end).total_seconds() / 60
            if slot_duration >= 15:  # Minimum 15 minutes
                free_slots.append({
                    "start": last_event_end,
                    "end": work_end,
                    "duration_minutes": int(slot_duration)
                })
    else:
        # No events today - entire work day is free
        slot_duration = (work_end - work_start).total_seconds() / 60
        if slot_duration >= 15:
            free_slots.append({
                "start": work_start,
                "end": work_end,
                "duration_minutes": int(slot_duration)
            })
    
    # Format slots with time range, time of day, energy level
    formatted_slots = []
    for slot in free_slots:
        start_time = slot["start"]
        end_time = slot["end"]
        
        # Format time range
        start_str = start_time.strftime('%I:%M %p').lstrip('0')
        end_str = end_time.strftime('%I:%M %p').lstrip('0')
        time_range = f"{start_str} - {end_str}"
        
        # Determine time of day
        hour = start_time.hour
        if 6 <= hour < 10:
            time_of_day = "morning"
            energy_level = "high"
        elif 10 <= hour < 12:
            time_of_day = "mid-morning"
            energy_level = "high"
        elif 12 <= hour < 14:
            time_of_day = "lunch"
            energy_level = "medium"
        elif 14 <= hour < 17:
            time_of_day = "afternoon"
            energy_level = "medium"
        else:
            time_of_day = "evening"
            energy_level = "low"
        
        formatted_slots.append({
            "time_range": time_range,
            "duration_minutes": slot["duration_minutes"],
            "time_of_day": time_of_day,
            "energy_level": energy_level,
            "start": start_time,
            "end": end_time
        })
    
    return formatted_slots


async def match_tasks_to_free_slots(
    tasks: List[Task],
    free_slots: List[Dict[str, Any]],
    user_id: int,
    session
) -> List[Dict[str, Any]]:
    """
    Match tasks to free hours with AI-powered recommendations.
    According to COMPREHENSIVE_PLAN.md Section 7.
    """
    if not tasks or not free_slots:
        return []
    
    # Get AI prioritization
    prioritized_tasks = await ai_prioritize_tasks(session, user_id, tasks)
    
    recommendations = []
    
    for item in prioritized_tasks[:10]:  # Top 10 tasks
        task = item["task"]
        priority_score = item["priority_score"]
        reasoning = item["reasoning"]
        
        # Find matching free slots
        task_duration = task.estimated_duration or 60  # Default 1 hour
        
        matching_slots = []
        for slot in free_slots:
            # Check if task fits in slot
            if task_duration <= slot["duration_minutes"]:
                # Check if task has deadline and slot is before deadline
                if task.due_date:
                    if slot["start"] <= task.due_date:
                        matching_slots.append((slot, slot["duration_minutes"] >= task_duration * 1.5))
                    else:
                        continue  # Skip slots after deadline
                else:
                    matching_slots.append((slot, True))
        
        if matching_slots:
            # Select best matching slot
            # Prefer slots that are:
            # - Before deadline (if task has deadline)
            # - High energy for high priority tasks
            # - Adequate size for task duration
            
            best_slot = None
            best_score = -1
            
            for slot, has_buffer in matching_slots:
                score = 0
                
                # Energy match (high priority -> high energy)
                if task.priority in [TaskPriority.HIGH, TaskPriority.URGENT]:
                    if slot["energy_level"] == "high":
                        score += 10
                
                # Size match
                if has_buffer:
                    score += 5
                
                # Deadline proximity
                if task.due_date:
                    hours_until_deadline = (task.due_date - slot["start"]).total_seconds() / 3600
                    if 0 < hours_until_deadline < 24:
                        score += 15  # Urgent deadline
                    elif hours_until_deadline < 48:
                        score += 10  # Soon deadline
                
                # Time of day preference (morning for complex tasks)
                if task_duration > 60 and slot["time_of_day"] == "morning":
                    score += 5
                
                if score > best_score:
                    best_score = score
                    best_slot = slot
            
            if best_slot:
                recommendations.append({
                    "task": task,
                    "priority_score": priority_score,
                    "recommended_slot": best_slot,
                    "reasoning": reasoning,
                    "match_score": best_score
                })
    
    # Sort by match score and priority
    recommendations.sort(key=lambda x: (x["match_score"], x["priority_score"]), reverse=True)
    
    return recommendations[:5]  # Top 5 recommendations


def format_daily_kickoff_message(
    user: User,
    events: List[Dict[str, Any]],
    free_slots: List[Dict[str, Any]],
    recommendations: List[Dict[str, Any]],
    upcoming_deadlines: List[Task],
    yesterday_completed: List[Task] = None
) -> str:
    """Format comprehensive daily kickoff message according to COMPREHENSIVE_PLAN.md."""
    yesterday_completed = yesterday_completed or []
    
    message = "🌅 **Good Morning! Here's your day plan:**\n\n"
    
    # Today's Schedule
    message += "📅 **Today's Schedule:**\n"
    if events:
        for event in events[:10]:  # Top 10 events
            start_dt = parse_calendar_datetime(event.get('start'), user.timezone)
            if start_dt and start_dt.date() == datetime.utcnow().date():
                time_str = start_dt.strftime('%I:%M %p').lstrip('0')
                duration = ""
                if event.get('end'):
                    end_dt = parse_calendar_datetime(event.get('end'), user.timezone)
                    if end_dt:
                        duration_minutes = (end_dt - start_dt).total_seconds() / 60
                        if duration_minutes > 0:
                            hours = int(duration_minutes // 60)
                            mins = int(duration_minutes % 60)
                            if hours > 0:
                                duration = f" ({hours}h {mins}m)"
                            else:
                                duration = f" ({mins}m)"
                message += f"• {time_str} - {event.get('summary', 'No title')}{duration}\n"
    else:
        message += "No events scheduled.\n"
    message += "\n"
    
    # Free Hours Available
    message += "⏰ **Free Hours Available:**\n"
    if free_slots:
        for slot in free_slots[:6]:  # Top 6 slots
            message += f"• {slot['time_range']} ({slot['duration_minutes']} min) - {slot['time_of_day'].capitalize()}\n"
    else:
        message += "Your day is fully booked! 😅\n"
    message += "\n"
    
    # Recommended Tasks
    message += "📋 **Recommended Tasks for Today** (Based on Priority & Deadlines):\n\n"
    
    if recommendations:
        # Group by priority
        high_priority = [r for r in recommendations if r["task"].priority in [TaskPriority.HIGH, TaskPriority.URGENT]]
        medium_priority = [r for r in recommendations if r["task"].priority == TaskPriority.MEDIUM]
        low_priority = [r for r in recommendations if r["task"].priority == TaskPriority.LOW]
        
        if high_priority:
            message += "⭐ **HIGH PRIORITY** (Recommended Now):\n"
            for i, rec in enumerate(high_priority[:3], 1):
                task = rec["task"]
                slot = rec["recommended_slot"]
                due_str = ""
                if task.due_date:
                    due_date = task.due_date.date()
                    today = datetime.utcnow().date()
                    if due_date == today:
                        due_str = "due TODAY ⚠️"
                    elif due_date == today + timedelta(days=1):
                        due_str = "due tomorrow"
                    else:
                        due_str = f"due {task.due_date.strftime('%Y-%m-%d')}"
                
                message += f"{i}. **{task.title}** ({task.priority.value.capitalize()}, {due_str})\n"
                message += f"   💡 Suggested: {slot['time_range']} ({slot['duration_minutes']} min available)\n"
                message += f"   Reason: {rec['reasoning'][:100]}\n\n"
        
        if medium_priority:
            message += "🟡 **MEDIUM PRIORITY** (When You Have Time):\n"
            for i, rec in enumerate(medium_priority[:3], 1):
                task = rec["task"]
                slot = rec["recommended_slot"]
                message += f"{i}. **{task.title}**\n"
                message += f"   💡 Can fit in: {slot['time_range']} ({slot['duration_minutes']} min slot)\n\n"
        
        if low_priority:
            message += "🟢 **LOW PRIORITY** (Optional):\n"
            for i, rec in enumerate(low_priority[:2], 1):
                task = rec["task"]
                slot = rec["recommended_slot"]
                message += f"{i}. **{task.title}**\n"
                message += f"   💡 Available: {slot['time_range']}\n\n"
    else:
        message += "No tasks to recommend at the moment.\n\n"
    
    # Upcoming Deadlines
    message += "⏰ **Upcoming Deadlines:**\n"
    if upcoming_deadlines:
        for deadline in upcoming_deadlines[:5]:
            due_str = deadline.due_date.strftime('%Y-%m-%d') if deadline.due_date else "No deadline"
            priority_icon = "🔴" if deadline.priority == TaskPriority.HIGH else "🟡" if deadline.priority == TaskPriority.MEDIUM else "🟢"
            today = datetime.utcnow().date()
            if deadline.due_date:
                if deadline.due_date.date() == today:
                    due_str += " ⚠️ TODAY"
                elif deadline.due_date.date() < today:
                    due_str += " ⚠️ OVERDUE"
            message += f"• {priority_icon} {deadline.title} - Due: {due_str}\n"
    else:
        message += "No upcoming deadlines.\n"
    message += "\n"
    
    # Yesterday's Completed Tasks (if any)
    if yesterday_completed:
        message += "✅ **Yesterday's Completed Tasks:**\n"
        for task in yesterday_completed[:5]:
            message += f"• {task.title}\n"
        message += "\n"
    
    # Focus Strategy
    if recommendations:
        message += "💡 **Today's Focus Strategy:**\n"
        if high_priority:
            urgent = [r for r in high_priority if r["task"].due_date and r["task"].due_date.date() == datetime.utcnow().date()]
            if urgent:
                task = urgent[0]["task"]
                message += f"• Start with **{task.title}** (due today!) - Complete before lunch\n"
            else:
                task = high_priority[0]["task"]
                slot = high_priority[0]["recommended_slot"]
                message += f"• Prioritize **{task.title}** ({slot['time_range']})\n"
        message += "• Use small slots for quick tasks\n"
        message += "\n"
    
    message += "Ready to tackle the day? Let's go! 🚀\n\n"
    message += "Options: /tasks | /calendar"
    
    return message


async def send_daily_summaries():
    """Send enhanced daily kickoff summaries to all active users."""
    async with AsyncSessionLocal() as session:
        # Get all active users
        stmt = select(User).where(
            User.is_active == True,
            User.is_onboarded == True
        )
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        # Get bot application
        application = create_application()
        
        for user in users:
            try:
                # Check if it's around work start time (within 1 hour)
                now = datetime.utcnow()
                work_start = now.replace(hour=user.work_start_hour, minute=0, second=0, microsecond=0)
                
                # Only send if it's around work start time
                if abs((now - work_start).total_seconds()) > 3600:
                    continue
                
                await send_user_summary(session, user, application)
            except Exception as e:
                logger.error(f"Error sending daily summary to user {user.id}: {e}")


async def send_user_summary(session, user, application):
    """Send enhanced daily kickoff summary to a user."""
    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Get today's calendar events
        events = []
        if user.google_calendar_connected:
            try:
                events = await list_events(session, user.id, today_start, today_end, max_results=20)
            except Exception as e:
                logger.error(f"Error getting calendar events for user {user.id}: {e}")
        
        # Calculate free hours
        free_slots = calculate_free_hours(
            events,
            user.work_start_hour,
            user.work_end_hour,
            user.timezone or "UTC"
        )
        
        # Get all active tasks
        active_tasks = await get_tasks(session, user.id, status=None, limit=50)
        active_tasks = [t for t in active_tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]]
        
        # Match tasks to free slots with AI recommendations
        recommendations = await match_tasks_to_free_slots(
            active_tasks,
            free_slots,
            user.id,
            session
        )
        
        # Get upcoming deadlines (next 3 days)
        from tasks.priority_queue import get_upcoming_deadlines
        upcoming_deadlines = await get_upcoming_deadlines(session, user.id, days=3)
        
        # Get yesterday's completed tasks
        yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = yesterday_start + timedelta(days=1)
        
        from sqlalchemy import and_
        yesterday_tasks_stmt = select(Task).where(
            and_(
                Task.user_id == user.id,
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at >= yesterday_start,
                Task.completed_at < yesterday_end
            )
        )
        yesterday_result = await session.execute(yesterday_tasks_stmt)
        yesterday_completed = list(yesterday_result.scalars().all())
        
        # Format and send message
        message = format_daily_kickoff_message(
            user,
            events,
            free_slots,
            recommendations,
            upcoming_deadlines,
            yesterday_completed
        )
        
        # Send via Telegram
        await application.bot.send_message(
            chat_id=user.telegram_id,
            text=message,
            parse_mode="Markdown"
        )
        
        logger.info(f"Sent enhanced daily summary to user {user.id}")
    except Exception as e:
        logger.error(f"Error sending summary to user {user.id}: {e}", exc_info=True)


async def send_daily_kickoff_on_startup(user_id: int):
    """
    Send daily kickoff when bot starts (immediate summary for user).
    According to COMPREHENSIVE_PLAN.md - trigger fires on bot start.
    """
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_onboarded:
            return
        
        application = create_application()
        await send_user_summary(session, user, application)
