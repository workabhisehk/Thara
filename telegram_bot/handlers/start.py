"""
Start command and onboarding flow handler.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from telegram_bot.conversation import ConversationState, set_conversation_state, get_conversation_context, get_conversation_state
from telegram_bot.keyboards import get_pillar_keyboard, get_yes_no_keyboard
from telegram_bot.handlers.onboarding import show_pillar_selection, handle_onboarding_message

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    try:
        user = update.effective_user
        logger.info(f"Received /start command from user {user.id} ({user.username})")
        
        async with AsyncSessionLocal() as session:
            # Check if user exists
            stmt = select(User).where(User.telegram_id == user.id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if db_user and db_user.is_onboarded:
                # User already onboarded
                await update.message.reply_text(
                    "👋 Hi! Welcome back!\n\n"
                    f"Hello {user.first_name}! 👋\n\n"
                    "I'm **Thara**, your productivity assistant. How can I help you today?\n\n"
                    "Use /help to see available commands."
                )
            else:
                # New user or not onboarded
                if not db_user:
                    # Create new user
                    db_user = User(
                        telegram_id=user.id,
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name
                    )
                    session.add(db_user)
                    await session.commit()
                    await session.refresh(db_user)
                
                # Start onboarding flow according to COMPREHENSIVE_PLAN.md
                set_conversation_state(user.id, ConversationState.ONBOARDING_PILLARS)
                
                # Use the comprehensive onboarding flow
                async with AsyncSessionLocal() as session:
                    await show_pillar_selection(update, context, session, db_user)
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ ERROR in start_command handler!")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("Full traceback:")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        
        # Try to send error message to user
        try:
            await update.message.reply_text(
                f"⚠️ Error: {str(e)}\n\n"
                "Please try again or contact support."
            )
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")
        # Re-raise to trigger global error handler
        raise


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = """
📚 **Available Commands:**

/start - Start or restart the bot
/help - Show this help message
/settings - Manage your settings
/tasks - View and manage tasks
/calendar - Calendar operations
/insights - View adaptive learning insights

💬 **Natural Language:**
You can also just chat with me naturally! Try:
- "Add task: Prepare presentation for client meeting"
- "What's on my calendar today?"
- "Show me my tasks"
- "Schedule time for project review"

I'll understand and help you manage your productivity!
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle natural language messages."""
    try:
        user = update.effective_user
        text = update.message.text
        
        logger.info(f"Received message from user {user.id}: {text[:50]}...")
        
        # Get conversation state
        state = get_conversation_state(user.id)
        context_data = get_conversation_context(user.id)
        
        # Store conversation
        try:
            from memory.conversation_store import store_conversation
            async with AsyncSessionLocal() as session:
                await store_conversation(
                    session,
                    user_id=user.id,
                    message_id=update.message.message_id,
                    text=text,
                    is_from_user=True
                )
                await session.commit()
        except Exception as e:
            logger.warning(f"Could not store conversation: {e}")
        
        # Route based on state
        if state in [
            ConversationState.ONBOARDING,
            ConversationState.ONBOARDING_PILLARS,
            ConversationState.ONBOARDING_CUSTOM_PILLAR,
            ConversationState.ONBOARDING_WORK_HOURS,
            ConversationState.ONBOARDING_TIMEZONE,
            ConversationState.ONBOARDING_INITIAL_TASKS,
            ConversationState.ONBOARDING_HABITS,
            ConversationState.ONBOARDING_MOOD_TRACKING,
        ]:
            # Continue onboarding flow
            await handle_onboarding_message(update, context)
        elif state in [
            ConversationState.ADDING_TASK,
            ConversationState.ADDING_TASK_PILLAR,
            ConversationState.ADDING_TASK_PRIORITY,
            ConversationState.ADDING_TASK_DUE_DATE,
            ConversationState.ADDING_TASK_DURATION,
        ]:
            # Handle task creation flow
            from telegram_bot.handlers.tasks import handle_task_creation_message
            await handle_task_creation_message(update, context)
        elif state == ConversationState.SCHEDULING_TASK:
            # Handle manual scheduling input
            from telegram_bot.handlers.scheduling_messages import handle_scheduling_message
            await handle_scheduling_message(update, context)
        else:
            # Process natural language with AI
            await handle_natural_language(update, context)
            
    except Exception as e:
        logger.error(f"Error in handle_message: {e}", exc_info=True)
        # Always send a response, even on error
        try:
            await update.message.reply_text(
                "I encountered an error processing your message. Please try again or use /help."
            )
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")


async def handle_onboarding_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages during onboarding."""
    # This will be expanded with full onboarding flow
    await update.message.reply_text(
        "I'm processing your onboarding. Please use the buttons provided or /start to restart."
    )


async def handle_natural_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle natural language with AI - conversational understanding throughout."""
    try:
        user = update.effective_user
        text = update.message.text if update.message else "No text"
        
        logger.info(f"🔵 Processing natural language message from user {user.id}: '{text[:100]}'")
        
        # Get conversation history for context
        from memory.context_retrieval import get_context_for_ai
        from database.connection import AsyncSessionLocal
        
        try:
            async with AsyncSessionLocal() as session:
                # Get conversation context
                conversation_context = await get_context_for_ai(session, user.id, text)
                
                # Use AI to understand the conversation naturally
                from ai.conversation_understanding import understand_conversation
                
                # Get recent conversation history
                recent_conversations = []
                if conversation_context.get("recent_conversations"):
                    recent_conversations = [
                        f"{'User' if conv['is_from_user'] else 'Thara'}: {conv['text'][:100]}"
                        for conv in conversation_context["recent_conversations"][:3]
                    ]
                
                # Understand user's message using AI
                understanding = await understand_conversation(
                    text,
                    conversation_history=recent_conversations,
                    current_state=str(get_conversation_state(user.id))
                )
                
                intent = understanding.get("intent", "general_chat")
                entities = understanding.get("entities", {})
                confidence = understanding.get("confidence", 0.5)
                action = understanding.get("action", "respond")
                
                logger.info(f"✅ Understood: intent={intent}, confidence={confidence}, action={action}")
                
                # Handle based on understood intent and action
                if action == "create_task" or (intent == "add_task" and confidence >= 0.6):
                    # Route to natural language task creation
                    intent_result = {
                        "intent": intent,
                        "entities": entities,
                        "confidence": confidence
                    }
                    from telegram_bot.handlers.natural_language_tasks import handle_natural_language_task_creation
                    await handle_natural_language_task_creation(update, context, intent_result)
                    return
                
                elif action == "show_tasks" or intent == "show_tasks":
                    from telegram_bot.handlers.tasks import tasks_command
                    await tasks_command(update, context)
                    return
                
                elif action == "view_calendar" or intent in ["calendar_query", "schedule"]:
                    from telegram_bot.handlers.calendar_handler import calendar_command
                    await calendar_command(update, context)
                    return
                
                elif understanding.get("needs_clarification"):
                    # Generate clarifying response
                    from ai.conversation_understanding import generate_conversational_response
                    response = await generate_conversational_response(
                        text,
                        intent,
                        entities,
                        conversation_context
                    )
                    await update.message.reply_text(response)
                    return
                
                else:
                    # Generate conversational response using AI
                    from ai.conversation_understanding import generate_conversational_response
                    from ai.response_generation import generate_context_aware_response
                    
                    # Try conversational response first, fallback to context-aware
                    try:
                        response = await generate_conversational_response(
                            text,
                            intent,
                            entities,
                            {
                                "tasks": conversation_context.get("active_tasks", []),
                                "calendar_events": conversation_context.get("calendar_events", []),
                                "user_preferences": conversation_context.get("user_preferences", {})
                            }
                        )
                        await update.message.reply_text(response)
                    except Exception as e:
                        logger.warning(f"Conversational response failed, using context-aware: {e}")
                        # Fallback to context-aware response
                        response_text = await generate_context_aware_response(
                            text,
                            user.id,
                            intent,
                            entities,
                            session
                        )
                        await update.message.reply_text(response_text)
                        
        except Exception as ai_error:
            logger.error(f"❌ Error in AI processing: {ai_error}", exc_info=True)
            # Fallback: friendly conversational response
            try:
                await update.message.reply_text(
                    f"Hi! I'm **Thara**. I understand you said: '{text[:100]}'\n\n"
                    "I'm working on understanding that better. "
                    "You can tell me naturally what you need, or use commands like /tasks, /calendar, or /help.\n\n"
                    "Just chat with me - I'll understand! 😊"
                )
            except Exception:
                pass  # Failed to send message
            
    except Exception as e:
        logger.error(f"❌ Fatal error in handle_natural_language: {e}", exc_info=True)
        # Ensure we always send a response
        try:
            await update.message.reply_text(
                f"👋 I received your message but encountered an error.\n\n"
                "Please try /help or send your message again.\n\n"
                "If this persists, check the bot logs."
            )
        except Exception as send_error:
            logger.error(f"❌ Failed to send error response: {send_error}", exc_info=True)

