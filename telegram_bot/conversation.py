"""
Conversation state management.
"""
from enum import Enum
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


class ConversationState(str, Enum):
    """Conversation states according to COMPREHENSIVE_PLAN.md."""
    IDLE = "idle"
    NORMAL = "normal"
    
    # Onboarding states
    ONBOARDING = "onboarding"
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

