"""
Conversation state management with database-backed persistence.
Falls back to in-memory storage if database is unavailable.
"""
from enum import Enum
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """Conversation states according to COMPREHENSIVE_PLAN.md."""
    IDLE = "idle"
    NORMAL = "normal"
    
    # Onboarding states
    ONBOARDING = "onboarding"
    ONBOARDING_NAME = "onboarding_name"
    ONBOARDING_PILLARS = "onboarding_pillars"
    ONBOARDING_CUSTOM_PILLAR = "onboarding_custom_pillar"
    ONBOARDING_WORK_HOURS = "onboarding_work_hours"
    ONBOARDING_TIMEZONE = "onboarding_timezone"
    ONBOARDING_INITIAL_TASKS = "onboarding_initial_tasks"
    ONBOARDING_HABITS = "onboarding_habits"
    ONBOARDING_MOOD_TRACKING = "onboarding_mood_tracking"
    ONBOARDING_CALENDAR = "onboarding_calendar"
    
    # Task management states
    ADDING_TASK = "adding_task"
    ADDING_TASK_PILLAR = "adding_task_pillar"
    ADDING_TASK_PRIORITY = "adding_task_priority"
    ADDING_TASK_DUE_DATE = "adding_task_due_date"
    ADDING_TASK_DURATION = "adding_task_duration"
    EDITING_TASK = "editing_task"
    SCHEDULING_TASK = "scheduling_task"
    
    # Other states
    CLARIFYING = "clarifying"
    SETTINGS = "settings"


@dataclass
class ConversationContext:
    """Context for a conversation."""
    user_id: int
    state: ConversationState = ConversationState.IDLE
    data: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def update(self, **kwargs):
        """Update context data."""
        self.data.update(kwargs)
        self.last_updated = datetime.utcnow()
    
    def get(self, key: str, default=None):
        """Get value from context data."""
        return self.data.get(key, default)
    
    def clear(self):
        """Clear context data."""
        self.data.clear()
        self.state = ConversationState.IDLE


# In-memory conversation contexts (fallback if database unavailable)
_conversation_contexts: Dict[int, ConversationContext] = {}


async def get_conversation_context_from_db(user_id: int) -> Optional[ConversationContext]:
    """Get conversation context from database."""
    try:
        from database.connection import AsyncSessionLocal
        from database.models import User
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.telegram_id == user_id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if db_user and db_user.conversation_state:
                state = ConversationState(db_user.conversation_state)
                context_data = db_user.conversation_context or {}
                return ConversationContext(
                    user_id=user_id,
                    state=state,
                    data=context_data
                )
    except Exception as e:
        logger.warning(f"Failed to get conversation context from DB for user {user_id}: {e}")
    return None


async def save_conversation_context_to_db(user_id: int, context: ConversationContext):
    """Save conversation context to database."""
    try:
        from database.connection import AsyncSessionLocal
        from database.models import User
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.telegram_id == user_id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if db_user:
                db_user.conversation_state = context.state.value
                db_user.conversation_context = context.data
                await session.commit()
                logger.debug(f"Saved conversation state to DB for user {user_id}: {context.state.value}")
    except Exception as e:
        logger.warning(f"Failed to save conversation context to DB for user {user_id}: {e}")


def get_conversation_context(user_id: int, use_db: bool = True) -> ConversationContext:
    """Get or create conversation context for user. Tries database first, falls back to in-memory."""
    # Try database first if enabled
    if use_db:
        try:
            import asyncio
            # Try to get from database (sync wrapper for async)
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # If loop is running, we're in async context - use in-memory for now
                # The async version will be called separately
                pass
            else:
                context = loop.run_until_complete(get_conversation_context_from_db(user_id))
                if context:
                    # Cache in memory
                    _conversation_contexts[user_id] = context
                    return context
        except Exception as e:
            logger.debug(f"Could not get context from DB (may be in async context): {e}")
    
    # Fallback to in-memory
    if user_id not in _conversation_contexts:
        _conversation_contexts[user_id] = ConversationContext(user_id=user_id)
    return _conversation_contexts[user_id]


async def get_conversation_context_async(user_id: int, use_db: bool = True) -> ConversationContext:
    """Async version of get_conversation_context."""
    if use_db:
        context = await get_conversation_context_from_db(user_id)
        if context:
            _conversation_contexts[user_id] = context
            return context
    
    # Fallback to in-memory
    if user_id not in _conversation_contexts:
        _conversation_contexts[user_id] = ConversationContext(user_id=user_id)
    return _conversation_contexts[user_id]


def set_conversation_state(user_id: int, state: ConversationState, save_to_db: bool = True):
    """Set conversation state for user. Saves to database if enabled."""
    context = get_conversation_context(user_id, use_db=False)  # Get from memory first
    context.state = state
    
    # Save to database asynchronously if enabled
    if save_to_db:
        try:
            import asyncio
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if not loop.is_running():
                loop.run_until_complete(save_conversation_context_to_db(user_id, context))
        except Exception as e:
            logger.debug(f"Could not save state to DB (may be in async context): {e}")


async def set_conversation_state_async(user_id: int, state: ConversationState, save_to_db: bool = True):
    """Async version of set_conversation_state."""
    context = await get_conversation_context_async(user_id, use_db=False)
    context.state = state
    
    if save_to_db:
        await save_conversation_context_to_db(user_id, context)


def get_conversation_state(user_id: int) -> ConversationState:
    """Get conversation state for user. Tries database first, falls back to in-memory."""
    context = get_conversation_context(user_id)
    return context.state


async def get_conversation_state_async(user_id: int) -> ConversationState:
    """Async version of get_conversation_state."""
    context = await get_conversation_context_async(user_id)
    return context.state


def clear_conversation_context(user_id: int):
    """Clear conversation context for user."""
    if user_id in _conversation_contexts:
        _conversation_contexts[user_id].clear()
    
    # Also clear from database
    try:
        import asyncio
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if not loop.is_running():
            async def clear_db():
                from database.connection import AsyncSessionLocal
                from database.models import User
                from sqlalchemy import select
                
                async with AsyncSessionLocal() as session:
                    stmt = select(User).where(User.telegram_id == user_id)
                    result = await session.execute(stmt)
                    db_user = result.scalar_one_or_none()
                    if db_user:
                        db_user.conversation_state = "idle"
                        db_user.conversation_context = None
                        await session.commit()
            
            loop.run_until_complete(clear_db())
    except Exception as e:
        logger.debug(f"Could not clear state from DB: {e}")

