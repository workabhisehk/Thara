"""
Conversation state management.
"""
from enum import Enum
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


class ConversationState(str, Enum):
    """Conversation states."""
    IDLE = "idle"
    ONBOARDING = "onboarding"
    ONBOARDING_PILLARS = "onboarding_pillars"
    ONBOARDING_WORK_HOURS = "onboarding_work_hours"
    ONBOARDING_TASKS = "onboarding_tasks"
    ONBOARDING_CALENDAR = "onboarding_calendar"
    ADDING_TASK = "adding_task"
    SCHEDULING_TASK = "scheduling_task"
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


# In-memory conversation contexts (in production, use Redis or database)
_conversation_contexts: Dict[int, ConversationContext] = {}


def get_conversation_context(user_id: int) -> ConversationContext:
    """Get or create conversation context for user."""
    if user_id not in _conversation_contexts:
        _conversation_contexts[user_id] = ConversationContext(user_id=user_id)
    return _conversation_contexts[user_id]


def set_conversation_state(user_id: int, state: ConversationState):
    """Set conversation state for user."""
    context = get_conversation_context(user_id)
    context.state = state


def get_conversation_state(user_id: int) -> ConversationState:
    """Get conversation state for user."""
    context = get_conversation_context(user_id)
    return context.state


def clear_conversation_context(user_id: int):
    """Clear conversation context for user."""
    if user_id in _conversation_contexts:
        _conversation_contexts[user_id].clear()

