"""
Calendar Agent: Handles calendar and scheduling operations.
Manages calendar viewing, task scheduling, availability checking, and calendar sync.
"""
import logging
from typing import Literal
from langgraph.types import Command
from agents_langgraph.state import AgentState

from telegram_bot.conversation import ConversationState

logger = logging.getLogger(__name__)


async def calendar_agent(state: AgentState) -> Command[Literal["calendar_agent", "task_agent", "router_agent", "human", "__end__"]]:
    """
    Calendar agent - handles all calendar and scheduling operations.
    
    Manages:
    - Viewing calendar events
    - Scheduling tasks in calendar
    - Checking availability
    - Suggesting time slots
    - Calendar sync operations
    - Conflict detection
    
    Can handoff to:
    - task_agent: After scheduling, return to task context
    - router_agent: General calendar query
    - human: Needs clarification or user input
    - __end__: Complete calendar operation
    """
    try:
        user_id = state.get("user_id")
        current_state = state.get("current_state")
        messages = state.get("messages", [])
        intent = state.get("intent")
        entities = state.get("entities", {})
        context = state.get("context", {})
        
        if not messages:
            logger.warning(f"CalendarAgent: No messages for user {user_id}")
            return Command(goto="__end__")
        
        last_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
        
        logger.info(f"CalendarAgent: Processing for user {user_id}, intent: {intent}")
        
        # Check if this is a task scheduling request from task_agent
        if context.get("task_scheduling"):
            logger.info(f"CalendarAgent: Task scheduling handoff from task_agent")
            task_entities = context.get("task_entities", {})
            
            # Store scheduling context
            state["agent_data"]["calendar"] = {
                "operation": "schedule_task",
                "task_entities": task_entities,
                "message": last_message
            }
            
            # If we have a scheduled time, proceed with scheduling
            # Otherwise, continue scheduling flow
            if current_state == ConversationState.SCHEDULING_TASK:
                return Command(
                    goto="__end__",
                    update={
                        "active_agent": "calendar_agent",
                        "agent_data": state["agent_data"]
                    }
                )
            
            # Schedule task will be handled by existing scheduling handler
            return Command(
                goto="__end__",
                update={
                    "active_agent": "calendar_agent",
                    "agent_data": state["agent_data"]
                }
            )
        
        # Map intents to calendar operations
        calendar_operations = {
            "view_calendar": "view",
            "calendar_query": "view",
            "schedule": "schedule",
            "schedule_task": "schedule",
            "check_availability": "check",
            "sync_calendar": "sync",
        }
        
        operation = calendar_operations.get(intent, "view")
        
        # Store calendar operation in agent data
        state["agent_data"]["calendar"] = {
            "operation": operation,
            "intent": intent,
            "entities": entities,
            "message": last_message
        }
        
        # For scheduling operations, may need task context
        if operation == "schedule" and not context.get("task_scheduling"):
            # Might need to create task first or get task ID
            # For now, continue with scheduling
            logger.info(f"CalendarAgent: Scheduling operation")
            return Command(
                goto="__end__",
                update={
                    "active_agent": "calendar_agent",
                    "agent_data": state["agent_data"]
                }
            )
        
        # For view operations
        if operation == "view":
            logger.info(f"CalendarAgent: Calendar viewing requested")
            # Calendar viewing will be handled by existing calendar handler
            return Command(
                goto="__end__",
                update={
                    "active_agent": "calendar_agent",
                    "agent_data": state["agent_data"]
                }
            )
        
        # Default: complete operation
        return Command(
            goto="__end__",
            update={
                "active_agent": "calendar_agent",
                "agent_data": state["agent_data"]
            }
        )
        
    except Exception as e:
        logger.error(f"CalendarAgent: Error: {e}", exc_info=True)
        return Command(
            goto="human",
            update={
                "error": str(e),
                "clarification_message": "I encountered an error processing your calendar request. Please try again.",
                "active_agent": "human"
            }
        )

