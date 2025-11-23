"""
Parlant tools for task management, calendar, and user operations.
These tools are registered with Parlant agents to enable reliable task completion.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import parlant.sdk as p
from database.connection import AsyncSessionLocal
from database.models import User, Task, TaskStatus, TaskPriority, PillarType
from tasks.service import create_task, get_tasks, update_task, delete_task
from google_calendar.client import list_events, create_event
from sqlalchemy import select

logger = logging.getLogger(__name__)


@p.tool
async def get_user_tasks(context: p.ToolContext, status: str = "active") -> p.ToolResult:
    """
    Get user's tasks. Status can be 'active', 'completed', or 'all'.
    
    Args:
        context: Parlant tool context (contains user_id)
        status: Task status filter ('active', 'completed', 'all')
    
    Returns:
        ToolResult with formatted task list
    """
    try:
        # Extract user_id from Parlant ToolContext
        # ToolContext should have access to customer/session
        user_id = None
        
        # Try to get from customer_id in context
        if hasattr(context, 'customer_id'):
            from agents_parlant.agent import _customer_to_user_id
            user_id = _customer_to_user_id.get(context.customer_id)
        
        # Try to get from customer object
        if not user_id and hasattr(context, 'customer'):
            customer = context.customer
            if hasattr(customer, 'id'):
                from agents_parlant.agent import _customer_to_user_id
                user_id = _customer_to_user_id.get(customer.id)
        
        # Try to get from session
        if not user_id and hasattr(context, 'session'):
            session = context.session
            if hasattr(session, 'customer_id'):
                from agents_parlant.agent import _customer_to_user_id
                user_id = _customer_to_user_id.get(session.customer_id)
        
        # Fallback: try direct user_id attribute
        if not user_id and hasattr(context, 'user_id'):
            user_id = context.user_id
        
        if not user_id:
            logger.error(f"Could not extract user_id from context. Context attributes: {dir(context)}")
            return p.ToolResult("Error: Could not identify user. Please try again.")
        async with AsyncSessionLocal() as session:
            # Get database user ID from telegram_id
            stmt = select(User).where(User.telegram_id == user_id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                return p.ToolResult("User not found. Please complete onboarding first.")
            
            # Map status
            status_map = {
                "active": TaskStatus.PENDING,
                "completed": TaskStatus.COMPLETED,
                "all": None
            }
            status_filter = status_map.get(status.lower(), TaskStatus.PENDING)
            
            tasks = await get_tasks(session, db_user.id, status=status_filter)
            
            if not tasks:
                return p.ToolResult("You have no tasks." if status == "active" else f"No {status} tasks found.")
            
            # Format tasks
            result_text = f"Your {status} tasks:\n\n"
            for i, task in enumerate(tasks[:20], 1):  # Limit to 20 tasks
                priority_emoji = {
                    TaskPriority.HIGH: "🔴",
                    TaskPriority.MEDIUM: "🟡",
                    TaskPriority.LOW: "🟢"
                }.get(task.priority, "⚪")
                
                due_date_str = ""
                if task.due_date:
                    due_date_str = f" (Due: {task.due_date.strftime('%Y-%m-%d %H:%M')})"
                
                result_text += f"{i}. {priority_emoji} {task.title}{due_date_str}\n"
                if task.description:
                    result_text += f"   {task.description[:100]}\n"
            
            if len(tasks) > 20:
                result_text += f"\n... and {len(tasks) - 20} more tasks."
            
            return p.ToolResult(result_text)
            
    except Exception as e:
        logger.error(f"Error in get_user_tasks: {e}", exc_info=True)
        return p.ToolResult(f"Error retrieving tasks: {str(e)}")


@p.tool
async def create_user_task(
    context: p.ToolContext,
    title: str,
    description: Optional[str] = None,
    pillar: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    estimated_duration: Optional[int] = None
) -> p.ToolResult:
    """
    Create a new task for the user.
    
    Args:
        context: Parlant tool context (contains user_id)
        title: Task title (required)
        description: Task description (optional)
        pillar: Task pillar - work, education, projects, personal, or other (optional)
        priority: Task priority - high, medium, or low (optional, defaults to medium)
        due_date: Due date in ISO format or natural language (optional)
        estimated_duration: Estimated duration in minutes (optional)
    
    Returns:
        ToolResult with task creation confirmation
    """
    try:
        # Extract user_id from context
        user_id = None
        if hasattr(context, 'user_id'):
            user_id = context.user_id
        elif hasattr(context, 'user') and hasattr(context.user, 'id'):
            user_id = context.user.id
        elif isinstance(context, dict):
            user_id = context.get('user_id')
        
        if not user_id:
            return p.ToolResult("Error: Could not identify user. Please try again.")
        
        async with AsyncSessionLocal() as session:
            # Get database user ID from telegram_id
            stmt = select(User).where(User.telegram_id == user_id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                return p.ToolResult("User not found. Please complete onboarding first.")
            
            # Parse due_date if provided
            parsed_due_date = None
            if due_date:
                try:
                    # Try ISO format first
                    parsed_due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                except:
                    try:
                        # Try parsing with dateutil
                        from dateutil import parser
                        parsed_due_date = parser.parse(due_date)
                    except:
                        logger.warning(f"Could not parse due_date: {due_date}")
            
            # Check for duplicates before creating
            from tasks.duplicate_detection import check_for_duplicates
            duplicate_info = await check_for_duplicates(
                session,
                db_user.id,
                title,
                parsed_due_date if due_date else None,
                similarity_threshold=0.85
            )
            
            # If duplicate found, return warning and don't create
            if duplicate_info and duplicate_info.get("is_duplicate"):
                warning_msg = duplicate_info.get("message", "Similar task found.")
                warning_msg += "\n\nPlease confirm if you want to create this task anyway, or update the existing one."
                return p.ToolResult(warning_msg)
            
            # Create task
            task = await create_task(
                session=session,
                user_id=db_user.id,
                title=title,
                description=description,
                pillar=pillar,
                priority=priority,
                due_date=parsed_due_date,
                estimated_duration=estimated_duration
            )
            
            await session.commit()
            
            priority_emoji = {
                TaskPriority.HIGH: "🔴 High",
                TaskPriority.MEDIUM: "🟡 Medium",
                TaskPriority.LOW: "🟢 Low"
            }.get(task.priority, "Medium")
            
            result_text = warning_prefix
            result_text += f"✅ Task created successfully!\n\n"
            result_text += f"**{task.title}**\n"
            if task.description:
                result_text += f"{task.description}\n"
            result_text += f"\nPriority: {priority_emoji}\n"
            result_text += f"Pillar: {task.pillar.value.capitalize()}\n"
            if task.due_date:
                result_text += f"Due: {task.due_date.strftime('%Y-%m-%d %H:%M')}\n"
            if task.estimated_duration:
                result_text += f"Estimated: {task.estimated_duration} minutes\n"
            
            return p.ToolResult(result_text)
            
    except ValueError as e:
        return p.ToolResult(f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in create_user_task: {e}", exc_info=True)
        return p.ToolResult(f"Error creating task: {str(e)}")


@p.tool
async def get_calendar_events(
    context: p.ToolContext,
    days: int = 7
) -> p.ToolResult:
    """
    Get user's calendar events for the next N days.
    
    Args:
        context: Parlant tool context (contains user_id)
        days: Number of days to look ahead (default: 7)
    
    Returns:
        ToolResult with formatted calendar events
    """
    try:
        # Extract user_id from context
        user_id = None
        if hasattr(context, 'user_id'):
            user_id = context.user_id
        elif hasattr(context, 'user') and hasattr(context.user, 'id'):
            user_id = context.user.id
        elif isinstance(context, dict):
            user_id = context.get('user_id')
        
        if not user_id:
            return p.ToolResult("Error: Could not identify user. Please try again.")
        
        async with AsyncSessionLocal() as session:
            # Get database user ID from telegram_id
            stmt = select(User).where(User.telegram_id == user_id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                return p.ToolResult("User not found. Please complete onboarding first.")
            
            # Check if calendar is connected
            if not db_user.google_calendar_connected:
                # Get OAuth URL for user
                try:
                    from google_calendar.auth import get_authorization_url
                    auth_url = get_authorization_url(db_user.id)
                    return p.ToolResult(
                        f"📅 **Google Calendar Not Connected**\n\n"
                        f"To access your calendar, please connect your Google Calendar account:\n\n"
                        f"🔗 [Click here to connect]({auth_url})\n\n"
                        f"After authorizing, I'll be able to show your calendar events and help you schedule tasks.\n\n"
                        f"**Note:** You'll need to authorize in a web browser, then use `/calendar` command to complete the connection."
                    )
                except Exception as auth_error:
                    logger.error(f"Error generating auth URL: {auth_error}")
                    return p.ToolResult(
                        f"📅 **Google Calendar Not Connected**\n\n"
                        f"To connect your calendar, use the `/calendar` command in Telegram. "
                        f"I'll provide you with a link to authorize access to your Google Calendar."
                    )
            
            events = await list_events(session, db_user.id, max_results=50)
            
            if not events:
                return p.ToolResult(f"No calendar events found for the next {days} days.")
            
            # Filter events within the specified days
            time_max = datetime.utcnow() + timedelta(days=days)
            filtered_events = []
            for event in events:
                event_start = event.get('start')
                if event_start:
                    try:
                        if isinstance(event_start, str):
                            event_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                        else:
                            event_dt = datetime.utcnow()  # Fallback
                        
                        if event_dt <= time_max:
                            filtered_events.append(event)
                    except:
                        filtered_events.append(event)  # Include if parsing fails
            
            if not filtered_events:
                return p.ToolResult(f"No calendar events found for the next {days} days.")
            
            # Format events
            result_text = f"📅 Your calendar events (next {days} days):\n\n"
            for i, event in enumerate(filtered_events[:20], 1):  # Limit to 20 events
                summary = event.get('summary', 'No title')
                start = event.get('start', '')
                location = event.get('location', '')
                
                result_text += f"{i}. {summary}\n"
                if start:
                    result_text += f"   📆 {start}\n"
                if location:
                    result_text += f"   📍 {location}\n"
                result_text += "\n"
            
            if len(filtered_events) > 20:
                result_text += f"... and {len(filtered_events) - 20} more events."
            
            return p.ToolResult(result_text)
            
    except ValueError as e:
        # Calendar not connected - provide helpful guidance
        error_msg = str(e)
        if "not connected" in error_msg.lower() or "credentials" in error_msg.lower():
            # Get OAuth URL for user
            try:
                from google_calendar.auth import get_authorization_url
                auth_url = get_authorization_url(db_user.id)
                return p.ToolResult(
                    f"📅 **Google Calendar Not Connected**\n\n"
                    f"To access your calendar, please connect your Google Calendar account:\n\n"
                    f"🔗 [Click here to connect]({auth_url})\n\n"
                    f"After authorizing, I'll be able to show your calendar events and help you schedule tasks.\n\n"
                    f"**Note:** You'll need to authorize in a web browser, then use `/calendar` command to complete the connection."
                )
            except Exception as auth_error:
                logger.error(f"Error generating auth URL: {auth_error}")
                return p.ToolResult(
                    f"📅 **Google Calendar Not Connected**\n\n"
                    f"To connect your calendar, use the `/calendar` command in Telegram. "
                    f"I'll provide you with a link to authorize access to your Google Calendar."
                )
        return p.ToolResult(f"Calendar error: {error_msg}")
    except Exception as e:
        logger.error(f"Error in get_calendar_events: {e}", exc_info=True)
        return p.ToolResult(f"Error retrieving calendar events: {str(e)}")


@p.tool
async def create_calendar_event(
    context: p.ToolContext,
    title: str,
    start_time: str,
    end_time: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None
) -> p.ToolResult:
    """
    Create a calendar event for the user.
    
    Args:
        context: Parlant tool context (contains user_id)
        title: Event title (required)
        start_time: Start time in ISO format or natural language (required)
        end_time: End time in ISO format or natural language (optional, defaults to 1 hour after start)
        description: Event description (optional)
        location: Event location (optional)
    
    Returns:
        ToolResult with event creation confirmation
    """
    try:
        # Extract user_id from context
        user_id = None
        if hasattr(context, 'user_id'):
            user_id = context.user_id
        elif hasattr(context, 'user') and hasattr(context.user, 'id'):
            user_id = context.user.id
        elif isinstance(context, dict):
            user_id = context.get('user_id')
        
        if not user_id:
            return p.ToolResult("Error: Could not identify user. Please try again.")
        
        async with AsyncSessionLocal() as session:
            # Get database user ID from telegram_id
            stmt = select(User).where(User.telegram_id == user_id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                return p.ToolResult("User not found. Please complete onboarding first.")
            
            # Parse start_time
            try:
                from dateutil import parser
                parsed_start = parser.parse(start_time)
            except:
                return p.ToolResult(f"Could not parse start_time: {start_time}. Please use ISO format or natural language.")
            
            # Parse end_time or default to 1 hour after start
            if end_time:
                try:
                    from dateutil import parser
                    parsed_end = parser.parse(end_time)
                except:
                    return p.ToolResult(f"Could not parse end_time: {end_time}. Please use ISO format or natural language.")
            else:
                parsed_end = parsed_start + timedelta(hours=1)
            
            # Create event
            event = await create_event(
                session=session,
                user_id=db_user.id,
                title=title,
                start_time=parsed_start,
                end_time=parsed_end,
                description=description,
                location=location
            )
            
            result_text = f"✅ Calendar event created successfully!\n\n"
            result_text += f"**{title}**\n"
            result_text += f"📆 {parsed_start.strftime('%Y-%m-%d %H:%M')} - {parsed_end.strftime('%H:%M')}\n"
            if location:
                result_text += f"📍 {location}\n"
            if description:
                result_text += f"\n{description}\n"
            
            return p.ToolResult(result_text)
            
    except ValueError as e:
        return p.ToolResult(f"Calendar not connected: {str(e)}")
    except Exception as e:
        logger.error(f"Error in create_calendar_event: {e}", exc_info=True)
        return p.ToolResult(f"Error creating calendar event: {str(e)}")


@p.tool
async def get_user_info(context: p.ToolContext) -> p.ToolResult:
    """
    Get user information and preferences.
    
    Args:
        context: Parlant tool context (contains user_id)
    
    Returns:
        ToolResult with user information
    """
    try:
        # Extract user_id from context
        user_id = None
        if hasattr(context, 'user_id'):
            user_id = context.user_id
        elif hasattr(context, 'user') and hasattr(context.user, 'id'):
            user_id = context.user.id
        elif isinstance(context, dict):
            user_id = context.get('user_id')
        
        if not user_id:
            return p.ToolResult("Error: Could not identify user. Please try again.")
        
        async with AsyncSessionLocal() as session:
            # Get database user ID from telegram_id
            stmt = select(User).where(User.telegram_id == user_id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                return p.ToolResult("User not found.")
            
            result_text = f"👤 User Information:\n\n"
            result_text += f"Name: {db_user.preferred_name or db_user.first_name or 'Not set'}\n"
            result_text += f"Onboarded: {'Yes' if db_user.is_onboarded else 'No'}\n"
            if db_user.timezone:
                result_text += f"Timezone: {db_user.timezone}\n"
            if db_user.work_hours:
                result_text += f"Work Hours: {db_user.work_hours}\n"
            
            return p.ToolResult(result_text)
            
    except Exception as e:
        logger.error(f"Error in get_user_info: {e}", exc_info=True)
        return p.ToolResult(f"Error retrieving user info: {str(e)}")

