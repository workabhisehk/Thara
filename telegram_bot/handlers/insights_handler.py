"""
Handler for adaptive learning insights and pattern notifications.
According to COMPREHENSIVE_PLAN.md Section 9: Adaptive Learning & Self-Improvement
"""
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from memory.adaptive_learning import (
    detect_recurring_patterns,
    suggest_automatic_flow,
    adapt_behavior_from_patterns
)
from memory.pattern_learning import get_user_habits

logger = logging.getLogger(__name__)


async def insights_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /insights command - show adaptive learning insights."""
    try:
        user = update.effective_user
        logger.info(f"Received /insights command from user {user.id}")
        
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.telegram_id == user.id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                await update.message.reply_text(
                    "❌ Please use /start first to set up your account."
                )
                return
            
            # Get adaptive behavior insights
            adaptations = await adapt_behavior_from_patterns(session, db_user.id)
            
            # Get detected patterns
            task_patterns = await detect_recurring_patterns(session, db_user.id, "task_creation")
            completion_patterns = await detect_recurring_patterns(session, db_user.id, "completion")
            scheduling_patterns = await detect_recurring_patterns(session, db_user.id, "scheduling")
            
            # Get user habits
            habits = await get_user_habits(session, db_user.id)
            
            # Build insights message
            message = "🧠 **Adaptive Learning Insights**\n\n"
            message += "I've been learning from your behavior patterns:\n\n"
            
            # Show detected patterns
            if task_patterns:
                message += "📋 **Recurring Patterns:**\n"
                for pattern in task_patterns[:3]:
                    if pattern["type"] == "recurring_task":
                        message += (
                            f"• Task pattern: '{pattern['pattern']}'\n"
                            f"  Frequency: Every {pattern['frequency_days']:.0f} days\n"
                            f"  Occurrences: {pattern['occurrences']}\n"
                            f"  Confidence: {pattern['confidence']:.0%}\n\n"
                        )
                message += "\n"
            
            if completion_patterns:
                message += "⏰ **Completion Patterns:**\n"
                for pattern in completion_patterns[:2]:
                    if pattern["type"] == "completion_time":
                        message += (
                            f"• Preferred completion time: {pattern['preferred_hour']}:00\n"
                            f"  Confidence: {pattern['confidence']:.0%}\n\n"
                        )
                message += "\n"
            
            if scheduling_patterns:
                message += "📅 **Scheduling Preferences:**\n"
                for pattern in scheduling_patterns[:2]:
                    if pattern["type"] == "scheduling_preference":
                        message += (
                            f"• Preferred scheduling time: {pattern['preferred_hour']}:00\n"
                            f"  Confidence: {pattern['confidence']:.0%}\n\n"
                        )
                message += "\n"
            
            # Show behavior adaptations
            if adaptations.get("check_in_timing") or adaptations.get("suggestion_timing"):
                message += "🔄 **Adapted Behaviors:**\n"
                if adaptations.get("check_in_timing"):
                    timing = adaptations["check_in_timing"]
                    message += f"• Check-in timing: {timing['suggested_hour']}:00 (confidence: {timing['confidence']:.0%})\n"
                if adaptations.get("suggestion_timing"):
                    timing = adaptations["suggestion_timing"]
                    message += f"• Suggestion timing: {timing['suggested_hour']}:00 (confidence: {timing['confidence']:.0%})\n"
                message += "\n"
            
            # Show habits
            if habits:
                message += "🎯 **Learned Habits:**\n"
                for habit in habits[:3]:
                    if habit.pattern_type == "preferred_pillar":
                        data = habit.pattern_data or {}
                        pillar = data.get("preferred_pillar", "unknown")
                        message += f"• Preferred category: {pillar.capitalize()} (confidence: {habit.confidence_score:.0%})\n"
                    elif habit.pattern_type == "task_completion_time":
                        data = habit.pattern_data or {}
                        avg_minutes = data.get("average_minutes", 0)
                        hours = int(avg_minutes // 60)
                        minutes = int(avg_minutes % 60)
                        if hours > 0:
                            message += f"• Average task duration: {hours}h {minutes}m (confidence: {habit.confidence_score:.0%})\n"
                        else:
                            message += f"• Average task duration: {minutes}m (confidence: {habit.confidence_score:.0%})\n"
                message += "\n"
            
            # Check for automatic flow suggestions
            flow_suggestions = []
            flow_patterns = []  # Store patterns for callback handling
            for pattern in task_patterns:
                if pattern.get("confidence", 0) > 0.7:
                    suggestion = await suggest_automatic_flow(session, db_user.id, pattern)
                    if suggestion:
                        flow_suggestions.append(suggestion)
                        flow_patterns.append(pattern)  # Store pattern for reference
            
            if flow_suggestions:
                # Store suggestions in conversation context for callback handling
                from telegram_bot.conversation import get_conversation_context
                conv_context = get_conversation_context(user.id)
                conv_context.data["flow_suggestions"] = flow_suggestions
                conv_context.data["flow_patterns"] = flow_patterns
                
                message += "💡 **Suggested Automations:**\n\n"
                keyboard = []
                for i, suggestion in enumerate(flow_suggestions[:3], 1):
                    message += f"{i}. {suggestion['description']}\n\n"
                    keyboard.append([InlineKeyboardButton(
                        f"✨ Enable {i}",
                        callback_data=f"enable_flow_{i}"
                    )])
                
                await update.message.reply_text(
                    message,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
                )
            else:
                message += "💡 No automatic flow suggestions at this time.\n\n"
                message += "Keep using the bot, and I'll learn more about your patterns!"
                
                await update.message.reply_text(
                    message,
                    parse_mode="Markdown"
                )
                
    except ImportError as e:
        if "greenlet" in str(e).lower() or "llama_index" in str(e).lower():
            logger.error(f"Missing dependency in insights_command: {e}", exc_info=True)
            missing = "greenlet" if "greenlet" in str(e).lower() else "llama_index"
            await update.message.reply_text(
                f"⚠️ Error: Missing dependency ({missing}). "
                "Please contact support or check your installation."
            )
        else:
            logger.error(f"Import error in insights_command: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ An error occurred while fetching insights. "
                "Please try again or use /help."
            )
    except Exception as e:
        logger.error(f"Error in insights_command: {e}", exc_info=True)
        error_msg = str(e).lower()
        if "greenlet" in error_msg:
            await update.message.reply_text(
                "⚠️ Error: Missing dependency (greenlet). "
                "Please contact support or check your installation."
            )
        elif "llama_index" in error_msg or "llama_index" in error_msg:
            await update.message.reply_text(
                "⚠️ Error: Missing dependency (llama_index). "
                "Insights feature requires llama_index. Please install it or contact support."
            )
        else:
            await update.message.reply_text(
                "❌ An error occurred while fetching insights. "
                "Please try again or use /help."
            )


async def notify_pattern_detected(
    session,
    user_id: int,
    pattern: dict,
    application
) -> None:
    """
    Notify user when a new pattern is detected.
    
    Args:
        session: Database session
        user_id: User ID
        pattern: Detected pattern dictionary
        application: Telegram application instance
    """
    try:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return
        
        # Only notify for high-confidence patterns
        if pattern.get("confidence", 0) < 0.7:
            return
        
        message = "🎯 **Pattern Detected!**\n\n"
        
        if pattern["type"] == "recurring_task":
            message += (
                f"I noticed you create tasks like '{pattern['pattern']}' "
                f"every {pattern['frequency_days']:.0f} days.\n\n"
                f"Would you like me to remind you automatically?"
            )
        elif pattern["type"] == "completion_time":
            message += (
                f"I noticed you tend to complete tasks around {pattern['preferred_hour']}:00.\n\n"
                f"Should I optimize my suggestions for this time?"
            )
        elif pattern["type"] == "scheduling_preference":
            message += (
                f"I noticed you prefer scheduling tasks around {pattern['preferred_hour']}:00.\n\n"
                f"Should I use this as your default scheduling time?"
            )
        
        # Create keyboard for action
        keyboard = [[
            InlineKeyboardButton("✨ Learn More", callback_data="insights_view"),
            InlineKeyboardButton("❌ Dismiss", callback_data="dismiss_pattern")
        ]]
        
        await application.bot.send_message(
            chat_id=user.telegram_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        logger.info(f"Notified user {user_id} about detected pattern: {pattern['type']}")
        
    except Exception as e:
        logger.error(f"Error notifying user about pattern: {e}")


async def handle_insights_callbacks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle callback queries from insights interface."""
    query = update.callback_query
    callback_data = query.data
    user = update.effective_user
    
    await query.answer()
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await query.message.reply_text("Please start with /start first.")
            return
        
        if callback_data.startswith("enable_flow_"):
            # Format: "enable_flow_1", "enable_flow_2", etc.
            flow_index = int(callback_data.replace("enable_flow_", "")) - 1
            
            # Get flow suggestions from conversation context or regenerate
            from telegram_bot.conversation import get_conversation_context
            conv_context = get_conversation_context(user.id)
            flow_suggestions = conv_context.data.get("flow_suggestions", [])
            
            # If not in context, regenerate (shouldn't happen, but safe fallback)
            if not flow_suggestions:
                task_patterns = await detect_recurring_patterns(session, db_user.id, "task_creation")
                for pattern in task_patterns:
                    if pattern.get("confidence", 0) > 0.7:
                        suggestion = await suggest_automatic_flow(session, db_user.id, pattern)
                        if suggestion:
                            flow_suggestions.append(suggestion)
            
            if flow_index < len(flow_suggestions):
                suggestion = flow_suggestions[flow_index]
                
                # Get corresponding pattern from context
                flow_patterns = conv_context.data.get("flow_patterns", [])
                pattern = flow_patterns[flow_index] if flow_index < len(flow_patterns) else None
                
                if pattern and suggestion.get("flow_type") == "recurring_task":
                    # Enable the recurring task flow
                    from memory.flow_enabler import enable_recurring_task_flow
                    
                    result = await enable_recurring_task_flow(
                        session,
                        db_user.id,
                        pattern,
                        suggestion
                    )
                    
                    await session.commit()
                    
                    if result.get("success"):
                        frequency_days = result.get("frequency_days", 0)
                        next_reminder = result.get("next_reminder")
                        next_reminder_str = next_reminder.strftime('%Y-%m-%d') if next_reminder else "soon"
                        
                        await query.message.edit_text(
                            f"✨ **Flow Enabled!**\n\n"
                            f"{suggestion['description']}\n\n"
                            f"I'll remind you every {frequency_days:.0f} days to create this task.\n\n"
                            f"**Next reminder:** {next_reminder_str}\n\n"
                            "You'll receive a notification when it's time to create the task again.",
                            parse_mode="Markdown"
                        )
                        
                        logger.info(f"User {user.id} enabled flow: {suggestion['flow_type']}")
                    else:
                        await query.message.edit_text(
                            f"❌ **Error Enabling Flow**\n\n"
                            f"Could not enable the flow. Please try again later.\n\n"
                            f"Error: {result.get('error', 'Unknown error')}",
                            parse_mode="Markdown"
                        )
                else:
                    # Other flow types - acknowledge but note limitation
                    await query.message.edit_text(
                        f"✨ **Flow Preferences Saved!**\n\n"
                        f"{suggestion['description']}\n\n"
                        "I'll adapt my suggestions based on this preference.\n\n"
                        "Note: Full automation for this flow type is coming soon!",
                        parse_mode="Markdown"
                    )
                    
                    logger.info(f"User {user.id} enabled flow preference: {suggestion['flow_type']}")
            else:
                await query.answer("❌ Flow not found", show_alert=True)
        
        elif callback_data == "insights_view":
            # Redirect to /insights command
            await query.message.edit_text(
                "📊 Loading your insights...\n\n"
                "Use /insights to see detailed adaptive learning insights."
            )
            # Trigger insights command
            from telegram_bot.handlers.insights_handler import insights_command
            # Create a fake update with message for the command
            fake_update = Update(
                update_id=update.update_id,
                message=query.message
            )
            await insights_command(fake_update, context)
        
        elif callback_data == "dismiss_pattern":
            await query.message.edit_text(
                "✅ Pattern notification dismissed.\n\n"
                "I'll continue learning from your patterns in the background. "
                "Use /insights to see your insights anytime."
            )
            logger.info(f"User {user.id} dismissed pattern notification")
        
        elif callback_data.startswith("create_recurring_task_"):
            # Format: "create_recurring_task_{habit_id}"
            habit_id = int(callback_data.replace("create_recurring_task_", ""))
            
            from memory.flow_enabler import create_recurring_task_from_flow
            
            task = await create_recurring_task_from_flow(
                session,
                db_user.id,
                habit_id
            )
            
            if task:
                await session.commit()
                
                await query.message.edit_text(
                    f"✅ **Task Created!**\n\n"
                    f"**{task.title}**\n\n"
                    "The task has been created based on your recurring pattern.\n\n"
                    "You can edit it, set a due date, or add more details.",
                    parse_mode="Markdown"
                )
                
                logger.info(f"User {user.id} created recurring task {task.id} from flow {habit_id}")
            else:
                await query.answer("❌ Error creating task", show_alert=True)
        
        elif callback_data.startswith("remind_later_"):
            # Format: "remind_later_{habit_id}"
            habit_id = int(callback_data.replace("remind_later_", ""))
            
            # Get habit and update next reminder time (delay by 1 day)
            from database.models import Habit
            habit = await session.get(Habit, habit_id)
            
            if habit and habit.user_id == db_user.id:
                from datetime import timedelta
                if habit.pattern_data:
                    next_reminder = datetime.utcnow() + timedelta(days=1)
                    habit.pattern_data["next_reminder"] = next_reminder.isoformat()
                    await session.flush()
                    await session.commit()
                
                await query.message.edit_text(
                    "✅ **Reminder Scheduled**\n\n"
                    "I'll remind you again tomorrow about this recurring task."
                )
                logger.info(f"User {user.id} delayed reminder for flow {habit_id}")
            else:
                await query.answer("❌ Flow not found", show_alert=True)

