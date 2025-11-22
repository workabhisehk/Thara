"""
LangGraph state schema for Thara productivity agent.
Extends MessagesState with additional context for multi-agent coordination.
"""
import logging
from typing import TypedDict, List, Optional, Dict, Any, Literal, Annotated
from datetime import datetime
from langgraph.graph import MessagesState, add_messages
from telegram_bot.conversation import ConversationState

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """
    Extended state for Thara multi-agent system.
    
    Extends MessagesState with custom fields for agent coordination.
    """
    # Messages from MessagesState
    messages: Annotated[List[Any], add_messages]
    
    # Current conversation state (mapped from ConversationState enum)
    current_state: ConversationState
    
    # Active agent (for tracking which agent is handling the conversation)
    active_agent: Optional[str]
    
    # User context
    user_id: Optional[int]
    telegram_update: Optional[Dict[str, Any]]  # Serialized Telegram Update
    
    # Intent and entities extracted by RouterAgent
    intent: Optional[str]
    entities: Optional[Dict[str, Any]]
    confidence: float
    
    # Context for agents (shared across agents)
    context: Dict[str, Any]
    
    # Agent-specific data (isolated per agent)
    agent_data: Dict[str, Dict[str, Any]]
    
    # Flow control
    needs_clarification: bool
    clarification_message: Optional[str]
    
    # Handoff control (for multi-agent transitions)
    handoff_to: Optional[str]
    handoff_reason: Optional[str]
    
    # Error handling
    error: Optional[str]
    error_recovery_attempts: int
    
    # Learning and adaptation
    corrections: List[Dict[str, Any]]
    feedback: Optional[Dict[str, Any]]
    
    # Metadata
    metadata: Dict[str, Any]


def create_initial_state(
    user_id: int,
    message: str,
    telegram_update: Optional[Dict[str, Any]] = None,
    current_state: ConversationState = ConversationState.NORMAL
) -> AgentState:
    """
    Create initial state for a new conversation turn.
    
    Args:
        user_id: Telegram user ID
        message: User's message text
        telegram_update: Serialized Telegram Update object
        current_state: Current conversation state
    
    Returns:
        Initialized AgentState
    """
    from langchain_core.messages import HumanMessage
    
    return {
        "messages": [HumanMessage(content=message)],
        "current_state": current_state,
        "active_agent": None,
        "user_id": user_id,
        "telegram_update": telegram_update or {},
        "intent": None,
        "entities": None,
        "confidence": 0.0,
        "context": {},
        "agent_data": {},
        "needs_clarification": False,
        "clarification_message": None,
        "handoff_to": None,
        "handoff_reason": None,
        "error": None,
        "error_recovery_attempts": 0,
        "corrections": [],
        "feedback": None,
        "metadata": {},
    }


def update_state_from_context(
    state: AgentState,
    user_id: int,
    conversation_state: ConversationState,
    context_data: Dict[str, Any]
) -> AgentState:
    """
    Update LangGraph state from existing conversation context.
    
    Args:
        state: Current LangGraph state
        user_id: Telegram user ID
        conversation_state: Current conversation state
        context_data: Context data from ConversationContext
    
    Returns:
        Updated AgentState
    """
    state["user_id"] = user_id
    state["current_state"] = conversation_state
    state["context"].update(context_data)
    
    # Map legacy state to active agent
    state_mapping = {
        ConversationState.ONBOARDING: "onboarding_agent",
        ConversationState.ONBOARDING_PILLARS: "onboarding_agent",
        ConversationState.ONBOARDING_CUSTOM_PILLAR: "onboarding_agent",
        ConversationState.ONBOARDING_WORK_HOURS: "onboarding_agent",
        ConversationState.ONBOARDING_TIMEZONE: "onboarding_agent",
        ConversationState.ONBOARDING_INITIAL_TASKS: "onboarding_agent",
        ConversationState.ONBOARDING_HABITS: "onboarding_agent",
        ConversationState.ONBOARDING_MOOD_TRACKING: "onboarding_agent",
        ConversationState.ADDING_TASK: "task_agent",
        ConversationState.ADDING_TASK_PILLAR: "task_agent",
        ConversationState.ADDING_TASK_PRIORITY: "task_agent",
        ConversationState.ADDING_TASK_DUE_DATE: "task_agent",
        ConversationState.ADDING_TASK_DURATION: "task_agent",
        ConversationState.EDITING_TASK: "task_agent",
        ConversationState.SCHEDULING_TASK: "calendar_agent",
        ConversationState.SETTINGS: "router_agent",
        ConversationState.NORMAL: None,  # Will be determined by router
    }
    
    state["active_agent"] = state_mapping.get(conversation_state)
    
    return state

