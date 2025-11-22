"""
Router Agent: Routes messages to appropriate specialized agents.
First agent in the flow - analyzes user intent and routes to the right agent.
"""
import logging
from typing import Literal
from langgraph.types import Command
from agents_langgraph.state import AgentState
from ai.intent_extraction import extract_intent
from ai.conversation_understanding import understand_conversation

logger = logging.getLogger(__name__)


async def router_agent(state: AgentState) -> Command[Literal["onboarding_agent", "task_agent", "calendar_agent", "adaptive_learning_agent", "human", "__end__"]]:
    """
    Router agent - analyzes user intent and routes to appropriate agent.
    
    Routes to:
    - onboarding_agent: User is in onboarding flow or starting onboarding
    - task_agent: Task-related queries (add, view, edit, delete tasks)
    - calendar_agent: Calendar/scheduling queries (view calendar, schedule task, check availability)
    - adaptive_learning_agent: Insights, patterns, learning-related queries
    - human: Needs clarification or user input
    - __end__: Complete and return response
    """
    try:
        user_id = state.get("user_id")
        current_state = state.get("current_state")
        messages = state.get("messages", [])
        
        if not messages:
            logger.warning(f"Router: No messages in state for user {user_id}")
            return Command(goto="__end__")
        
        # Get last user message
        last_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
        
        logger.info(f"Router: Analyzing intent for user {user_id}, state: {current_state}, message: {last_message[:100]}")
        
        # Check if user is in onboarding
        from telegram_bot.conversation import ConversationState
        onboarding_states = [
            ConversationState.ONBOARDING,
            ConversationState.ONBOARDING_PILLARS,
            ConversationState.ONBOARDING_CUSTOM_PILLAR,
            ConversationState.ONBOARDING_WORK_HOURS,
            ConversationState.ONBOARDING_TIMEZONE,
            ConversationState.ONBOARDING_INITIAL_TASKS,
            ConversationState.ONBOARDING_HABITS,
            ConversationState.ONBOARDING_MOOD_TRACKING,
        ]
        
        if current_state in onboarding_states:
            logger.info(f"Router: User {user_id} in onboarding state {current_state}, routing to onboarding_agent")
            return Command(
                goto="onboarding_agent",
                update={"active_agent": "onboarding_agent"}
            )
        
        # Use AI to understand intent
        from database.connection import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            try:
                # Use conversation understanding for natural language
                understanding = await understand_conversation(
                    last_message,
                    conversation_history=[str(m.content) for m in messages[:-1]] if len(messages) > 1 else [],
                    current_state=str(current_state)
                )
                
                intent = understanding.get("intent", "general_chat")
                entities = understanding.get("entities", {})
                confidence = understanding.get("confidence", 0.5)
                action = understanding.get("action", "respond")
                
                logger.info(f"Router: Intent={intent}, Action={action}, Confidence={confidence}")
                
                # Update state with extracted intent
                state_update = {
                    "intent": intent,
                    "entities": entities,
                    "confidence": confidence,
                    "needs_clarification": understanding.get("needs_clarification", False),
                }
                
                # Route based on intent and action
                if action == "onboarding" or intent == "start_onboarding":
                    return Command(
                        goto="onboarding_agent",
                        update={**state_update, "active_agent": "onboarding_agent"}
                    )
                
                elif action == "create_task" or (intent == "add_task" and confidence >= 0.6):
                    return Command(
                        goto="task_agent",
                        update={**state_update, "active_agent": "task_agent"}
                    )
                
                elif action == "show_tasks" or intent == "show_tasks" or intent == "view_tasks":
                    return Command(
                        goto="task_agent",
                        update={**state_update, "active_agent": "task_agent"}
                    )
                
                elif action == "view_calendar" or intent in ["calendar_query", "schedule", "schedule_task"]:
                    return Command(
                        goto="calendar_agent",
                        update={**state_update, "active_agent": "calendar_agent"}
                    )
                
                elif intent in ["insights", "patterns", "analytics", "learn"] or action == "view_insights":
                    return Command(
                        goto="adaptive_learning_agent",
                        update={**state_update, "active_agent": "adaptive_learning_agent"}
                    )
                
                elif understanding.get("needs_clarification"):
                    return Command(
                        goto="human",
                        update={
                            **state_update,
                            "clarification_message": understanding.get("clarification_message", "Could you clarify what you need?"),
                            "active_agent": "human"
                        }
                    )
                
                else:
                    # General chat - default to task_agent for now (can be enhanced)
                    logger.info(f"Router: General chat, defaulting to task_agent")
                    return Command(
                        goto="task_agent",
                        update={**state_update, "active_agent": "task_agent"}
                    )
                    
            except Exception as e:
                logger.error(f"Router: Error understanding intent: {e}", exc_info=True)
                # Fallback: route to task_agent
                return Command(
                    goto="task_agent",
                    update={
                        "intent": "general_chat",
                        "confidence": 0.3,
                        "error": str(e),
                        "active_agent": "task_agent"
                    }
                )
    
    except Exception as e:
        logger.error(f"Router: Fatal error: {e}", exc_info=True)
        return Command(
            goto="__end__",
            update={"error": str(e)}
        )

