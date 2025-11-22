"""
Calendar-related handlers.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from datetime import datetime, timedelta
from google_calendar.client import list_events
from google_calendar.auth import get_authorization_url

logger = logging.getLogger(__name__)


async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /calendar command - show user's calendar events."""
    try:
        user = update.effective_user
        logger.info(f"Received /calendar command from user {user.id}")
        
        async with AsyncSessionLocal() as session:
            # Check if user exists and is connected to Google Calendar
            stmt = select(User).where(User.telegram_id == user.id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                await update.message.reply_text(
                    "❌ Please use /start first to set up your account."
                )
                return
            
            # Check if Google Calendar is connected
            if not db_user.google_calendar_connected:
                # Not connected - provide OAuth link
                try:
                    auth_url = get_authorization_url(db_user.id)
                    await update.message.reply_text(
                        "📅 **Google Calendar Not Connected**\n\n"
                        "To view your calendar events, please connect your Google Calendar account:\n\n"
                        f"[Click here to connect]({auth_url})\n\n"
                        "After authorizing, use `/calendar` again to see your events.\n\n"
                        "**Note:** You'll need to authorize the bot in a web browser.",
                        parse_mode="Markdown",
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    logger.error(f"Error generating auth URL: {e}")
                    await update.message.reply_text(
                        "❌ Error setting up Google Calendar connection. "
                        "Please check your configuration or contact support."
                    )
                return
            
            # User is connected - fetch and display events
            try:
                # Get events for next 7 days
                time_min = datetime.utcnow()
                time_max = time_min + timedelta(days=7)
                
                events = await list_events(
                    session=session,
                    user_id=db_user.id,
                    time_min=time_min,
                    time_max=time_max,
                    max_results=20
                )
                
                if not events:
                    await update.message.reply_text(
                        "📅 **Your Calendar**\n\n"
                        "No events scheduled for the next 7 days.\n\n"
                        "Would you like to:\n"
                        "- Schedule a task? (coming soon)\n"
                        "- View past events? (coming soon)"
                    )
                    return
                
                # Format events message
                message = "📅 **Your Calendar (Next 7 Days)**\n\n"
                
                # Group events by date
                events_by_date = {}
                for event in events:
                    start_str = event.get('start', '')
                    try:
                        # Parse datetime or date
                        if 'T' in start_str:
                            start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                            date_key = start_dt.strftime('%Y-%m-%d')
                            time_str = start_dt.strftime('%H:%M')
                        else:
                            date_key = start_str
                            time_str = "All day"
                        
                        if date_key not in events_by_date:
                            events_by_date[date_key] = []
                        events_by_date[date_key].append((time_str, event))
                    except Exception as e:
                        logger.warning(f"Error parsing event time: {e}")
                        events_by_date.setdefault('Unknown', []).append(('', event))
                
                # Display events grouped by date
                sorted_dates = sorted(events_by_date.keys())
                for date_key in sorted_dates[:7]:  # Limit to 7 days
                    events_for_date = events_by_date[date_key]
                    events_for_date.sort(key=lambda x: x[0])  # Sort by time
                    
                    # Format date nicely
                    try:
                        date_obj = datetime.strptime(date_key, '%Y-%m-%d')
                        if date_obj.date() == datetime.utcnow().date():
                            date_display = "**Today**"
                        elif date_obj.date() == (datetime.utcnow() + timedelta(days=1)).date():
                            date_display = "**Tomorrow**"
                        else:
                            date_display = date_obj.strftime('%A, %B %d')
                    except:
                        date_display = date_key
                    
                    message += f"\n📆 {date_display}\n"
                    
                    for time_str, event in events_for_date:
                        summary = event.get('summary', 'No title')
                        location = event.get('location', '')
                        location_str = f"📍 {location}\n" if location else ""
                        message += f"  • {time_str}: **{summary}**\n{location_str}"
                
                # Truncate if too long (Telegram limit is 4096 chars)
                if len(message) > 4000:
                    message = message[:4000] + "\n\n... (showing first 20 events)"
                
                await update.message.reply_text(
                    message,
                    parse_mode="Markdown"
                )
                
                logger.info(f"Displayed {len(events)} calendar events for user {user.id}")
                
            except ValueError as e:
                # User not connected error
                logger.error(f"Calendar connection error: {e}")
                await update.message.reply_text(
                    "❌ Google Calendar connection error. "
                    "Please reconnect your calendar account."
                )
            except Exception as e:
                logger.error(f"Error fetching calendar events: {e}", exc_info=True)
                await update.message.reply_text(
                    f"❌ Error fetching calendar events: {str(e)}\n\n"
                    "Please try again or check your Google Calendar connection."
                )
                
    except ImportError as e:
        if "greenlet" in str(e).lower():
            logger.error(f"Greenlet error in calendar_command: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ Error: Missing dependency (greenlet). "
                "Please contact support or check your installation."
            )
        else:
            logger.error(f"Import error in calendar_command: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ An error occurred while fetching your calendar. "
                "Please try again or use /help."
            )
    except Exception as e:
        logger.error(f"Error in calendar_command: {e}", exc_info=True)
        error_msg = str(e).lower()
        if "greenlet" in error_msg:
            await update.message.reply_text(
                "⚠️ Error: Missing dependency (greenlet). "
                "Please contact support or check your installation."
            )
        else:
            await update.message.reply_text(
                "❌ An error occurred while fetching your calendar. "
                "Please try again or use /help."
            )


async def sync_calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sync_calendar command - manually sync calendar and show suggestions."""
    try:
        user = update.effective_user
        logger.info(f"Received /sync_calendar command from user {user.id}")
        
        async with AsyncSessionLocal() as session:
            # Check if user exists and is connected to Google Calendar
            stmt = select(User).where(User.telegram_id == user.id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                await update.message.reply_text(
                    "❌ Please use /start first to set up your account."
                )
                return
            
            if not db_user.google_calendar_connected:
                await update.message.reply_text(
                    "❌ Google Calendar is not connected.\n\n"
                    "Please connect your Google Calendar first using `/calendar`.",
                    parse_mode="Markdown"
                )
                return
            
            # Sync calendar
            await update.message.reply_text("🔄 Syncing your calendar...")
            
            from google_calendar.sync import sync_calendar, suggest_event_task_links
            
            stats = await sync_calendar(session, db_user.id)
            await session.commit()
            
            # Format sync results
            message = "✅ **Calendar Sync Complete**\n\n"
            message += f"📅 Events created: {stats['created']}\n"
            message += f"🔄 Events updated: {stats['updated']}\n"
            message += f"🔗 Events linked to tasks: {stats['linked']}\n"
            if stats['task_updated'] > 0:
                message += f"✅ Tasks updated from calendar: {stats['task_updated']}\n"
            if stats['errors'] > 0:
                message += f"⚠️ Errors: {stats['errors']}\n"
            
            # Get link suggestions
            suggestions = await suggest_event_task_links(session, db_user.id)
            
            if suggestions:
                message += "\n\n💡 **Suggested Links:**\n\n"
                message += "I found potential matches between calendar events and tasks:\n\n"
                
                for i, suggestion in enumerate(suggestions[:5], 1):
                    time_str = suggestion['event_time'].strftime('%b %d, %I:%M %p')
                    similarity = suggestion['similarity_score']
                    message += (
                        f"{i}. **{suggestion['event_title']}** ({time_str})\n"
                        f"   → Task: {suggestion['task_title']}\n"
                        f"   Match: {similarity:.0%} ({suggestion['reason']})\n\n"
                    )
                
                message += "Use `/link_event {event_id} {task_id}` to link them."
            else:
                message += "\n\n✅ No suggestions needed - everything looks good!"
            
            await update.message.reply_text(message, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"Error in sync_calendar_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred while syncing your calendar. "
            "Please try again or use /help."
        )

