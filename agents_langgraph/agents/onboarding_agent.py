"""
Onboarding Agent: Handles user onboarding flow.
Manages pillar selection, work hours, timezone, habits, mood tracking setup.
"""
import logging
from typing import Literal
from langgraph.types import Command
from agents_langgraph.state import AgentState

from telegram_bot.conversation import ConversationState

logger = logging.getLogger(__name__)


async def onboarding_agent(state: AgentState) -> Command[Literal["onboarding_agent", "router_agent", "human", "__end__"]]:
    """
    Onboarding agent - handles all onboarding-related interactions.
    
    Manages:
    - Pillar selection
    - Custom pillar creation
    - Work hours input
    - Timezone selection
    - Initial tasks setup
    - Habits setup
    - Mood tracking setup
    
    Can handoff to:
    - router_agent: Onboarding complete, return to normal flow
    - human: Needs user input or clarification
    - __end__: Complete onboarding response
    """
    try:
        user_id = state.get("user_id")
        current_state = state.get("current_state")
        messages = state.get("messages", [])
        
        if not messages:
            logger.warning(f"OnboardingAgent: No messages for user {user_id}")
            return Command(goto="__end__")
        
        last_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
        
        logger.info(f"OnboardingAgent: Processing for user {user_id}, state: {current_state}")
        
        # Import onboarding handlers
        from telegram_bot.handlers.onboarding import handle_onboarding_message
        from telegram import Update
        from telegram.ext import ContextTypes
        from database.connection import AsyncSessionLocal
        from database.models import User
        from sqlalchemy import select
        
        # Reconstruct Telegram Update from state (if available)
        telegram_update_data = state.get("telegram_update", {})
        
        # For now, we'll delegate to existing onboarding handler
        # In a full migration, we'd refactor handlers to work with LangGraph state
        
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.telegram_id == user_id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                # Create user if needed
                db_user = User(
                    telegram_id=user_id,
                    username=telegram_update_data.get("username"),
                    first_name=telegram_update_data.get("first_name"),
                    last_name=telegram_update_data.get("last_name")
                )
                session.add(db_user)
                await session.commit()
                await session.refresh(db_user)
            
            # Check if onboarding is complete
            if db_user.is_onboarded and current_state == ConversationState.NORMAL:
                logger.info(f"OnboardingAgent: User {user_id} already onboarded, routing to normal flow")
                return Command(
                    goto="router",
                    update={
                        "active_agent": "router",
                        "current_state": ConversationState.NORMAL
                    }
                )
            
            # Store response in state for Telegram handler to send
            # The existing onboarding handler will send the response via Telegram
            # We just track the state here
            
            # Determine next state based on current state and message
            onboarding_states = {
                ConversationState.ONBOARDING_PILLARS: "pillars",
                ConversationState.ONBOARDING_CUSTOM_PILLAR: "custom_pillar",
                ConversationState.ONBOARDING_WORK_HOURS: "work_hours",
                ConversationState.ONBOARDING_TIMEZONE: "timezone",
                ConversationState.ONBOARDING_INITIAL_TASKS: "initial_tasks",
                ConversationState.ONBOARDING_HABITS: "habits",
                ConversationState.ONBOARDING_MOOD_TRACKING: "mood_tracking",
            }
            
            # Store onboarding step in agent data
            onboarding_step = onboarding_states.get(current_state, "start")
            state["agent_data"]["onboarding"] = {
                "step": onboarding_step,
                "message": last_message
            }
            
            # If onboarding complete, handoff to router
            if db_user.is_onboarded:
                logger.info(f"OnboardingAgent: User {user_id} onboarding complete")
                return Command(
                    goto="router",
                    update={
                        "active_agent": "router",
                        "current_state": ConversationState.NORMAL,
                        "context": {
                            **state.get("context", {}),
                            "onboarding_complete": True
                        }
                    }
                )
            
            # Continue onboarding flow
            # Response will be sent by existing handlers
            return Command(
                goto="__end__",
                update={
                    "active_agent": "onboarding_agent",
                    "agent_data": state["agent_data"]
                }
            )
            
    except Exception as e:
        logger.error(f"OnboardingAgent: Error: {e}", exc_info=True)
        return Command(
            goto="human",
            update={
                "error": str(e),
                "clarification_message": "I encountered an error during onboarding. Please try again or use /start to restart.",
                "active_agent": "human"
            }
        )

