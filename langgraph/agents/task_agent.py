"""
Task Agent: Handles all task-related operations.
Manages task creation, viewing, editing, deletion, prioritization, and natural language task creation.
"""
import logging
from typing import Literal
from langgraph.types import Command
from langgraph.state import AgentState
from langgraph.graph import MessagesState
from telegram_bot.conversation import ConversationState

logger = logging.getLogger(__name__)


async def task_agent(state: AgentState) -> Command[Literal["task_agent", "calendar_agent", "router_agent", "human", "__end__"]]:
    """
    Task agent - handles all task-related operations.
    
    Manages:
    - Task creation (guided and natural language)
    - Task viewing and listing
    - Task editing and deletion
    - Task prioritization
    - Task scheduling (hands off to calendar_agent)
    - Task filtering and sorting
    
    Can handoff to:
    - calendar_agent: For scheduling tasks
    - router_agent: General query, redirect
    - human: Needs clarification
    - __end__: Complete task operation
    """
    try:
        user_id = state.get("user_id")
        current_state = state.get("current_state")
        messages = state.get("messages", [])
        intent = state.get("intent")
        entities = state.get("entities", {})
        confidence = state.get("confidence", 0.0)
        
        if not messages:
            logger.warning(f"TaskAgent: No messages for user {user_id}")
            return Command(goto="__end__")
        
        last_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
        
        logger.info(f"TaskAgent: Processing for user {user_id}, intent: {intent}, confidence: {confidence}")
        
        # Check if user wants to schedule a task
        if intent == "schedule_task" or "schedule" in last_message.lower():
            logger.info(f"TaskAgent: Task scheduling requested, handing off to calendar_agent")
            return Command(
                goto="calendar_agent",
                update={
                    "active_agent": "calendar_agent",
                    "handoff_to": "calendar_agent",
                    "handoff_reason": "Task scheduling requested",
                    "context": {
                        **state.get("context", {}),
                        "task_scheduling": True,
                        "task_entities": entities
                    }
                }
            )
        
        # Map intents to task operations
        task_operations = {
            "add_task": "create",
            "create_task": "create",
            "show_tasks": "view",
            "view_tasks": "view",
            "list_tasks": "view",
            "edit_task": "edit",
            "update_task": "edit",
            "delete_task": "delete",
            "complete_task": "complete",
            "prioritize_task": "prioritize",
        }
        
        operation = task_operations.get(intent, "view")
        
        # Store task operation in agent data
        state["agent_data"]["task"] = {
            "operation": operation,
            "intent": intent,
            "entities": entities,
            "confidence": confidence,
            "message": last_message
        }
        
        # Check if we're in task creation flow
        task_states = [
            ConversationState.ADDING_TASK,
            ConversationState.ADDING_TASK_PILLAR,
            ConversationState.ADDING_TASK_PRIORITY,
            ConversationState.ADDING_TASK_DUE_DATE,
            ConversationState.ADDING_TASK_DURATION,
        ]
        
        if current_state in task_states:
            # Continue task creation flow
            logger.info(f"TaskAgent: Continuing task creation flow, state: {current_state}")
            return Command(
                goto="__end__",
                update={
                    "active_agent": "task_agent",
                    "agent_data": state["agent_data"]
                }
            )
        
        # For natural language task creation with high confidence
        if operation == "create" and confidence >= 0.7:
            logger.info(f"TaskAgent: High confidence task creation, processing with AI")
            # Task creation will be handled by existing natural language handler
            return Command(
                goto="__end__",
                update={
                    "active_agent": "task_agent",
                    "agent_data": state["agent_data"]
                }
            )
        
        # For view/list operations
        if operation == "view":
            logger.info(f"TaskAgent: Task viewing requested")
            # Task viewing will be handled by existing tasks handler
            return Command(
                goto="__end__",
                update={
                    "active_agent": "task_agent",
                    "agent_data": state["agent_data"]
                }
            )
        
        # For other operations or low confidence, need clarification
        if confidence < 0.6:
            logger.info(f"TaskAgent: Low confidence ({confidence}), requesting clarification")
            return Command(
                goto="human",
                update={
                    "needs_clarification": True,
                    "clarification_message": "I understand you want to work with tasks. Could you be more specific? For example:\n"
                                           "• 'Add task: Prepare presentation'\n"
                                           "• 'Show my tasks'\n"
                                           "• 'Schedule my task for tomorrow'",
                    "active_agent": "human"
                }
            )
        
        # Default: complete operation
        return Command(
            goto="__end__",
            update={
                "active_agent": "task_agent",
                "agent_data": state["agent_data"]
            }
        )
        
    except Exception as e:
        logger.error(f"TaskAgent: Error: {e}", exc_info=True)
        return Command(
            goto="human",
            update={
                "error": str(e),
                "clarification_message": "I encountered an error processing your task request. Please try again.",
                "active_agent": "human"
            }
        )

