"""
Main LangGraph for Thara productivity agent.
Connects all specialized agents with routing and handoff logic.
"""
import logging
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from langgraph.state import (
    AgentState,
    create_initial_state,
    update_state_from_context
)
from langgraph.agents import (
    router_agent,
    onboarding_agent,
    task_agent,
    calendar_agent,
    adaptive_learning_agent,
    human_agent,
)
from telegram_bot.conversation import ConversationState, get_conversation_state, get_conversation_context

logger = logging.getLogger(__name__)

# Global checkpointer for conversation memory
checkpointer = MemorySaver()


def should_continue_after_router(state: AgentState) -> str:
    """
    Determine next node after router.
    Router agent returns Command with goto, but we need to check state.
    """
    handoff_to = state.get("handoff_to")
    if handoff_to and handoff_to != "__end__":
        return handoff_to
    
    active_agent = state.get("active_agent")
    if active_agent and active_agent != "__end__":
        return active_agent
    
    # Default to end if no routing specified
    return END


def should_continue_after_agent(state: AgentState) -> str:
    """
    Determine next node after any agent.
    Checks for handoffs or completion.
    """
    handoff_to = state.get("handoff_to")
    if handoff_to:
        if handoff_to == "__end__":
            return END
        return handoff_to
    
    # Default to end
    return END


def build_graph() -> StateGraph:
    """
    Build the main LangGraph with all agents.
    
    Graph structure:
    START -> router_agent -> [onboarding_agent | task_agent | calendar_agent | adaptive_learning_agent | human_agent] -> END
    """
    # Create graph with AgentState
    graph = StateGraph(AgentState)
    
    # Add all agent nodes
    graph.add_node("router", router_agent)
    graph.add_node("onboarding_agent", onboarding_agent)
    graph.add_node("task_agent", task_agent)
    graph.add_node("calendar_agent", calendar_agent)
    graph.add_node("adaptive_learning_agent", adaptive_learning_agent)
    graph.add_node("human", human_agent)
    
    # Set entry point
    graph.add_edge(START, "router")
    
    # Router can route to any agent or end
    # Since router returns Command, we need conditional edges
    # For now, we'll add direct edges and handle routing in agents
    
    # Router routes to specialized agents
    graph.add_conditional_edges(
        "router",
        should_continue_after_router,
        {
            "onboarding_agent": "onboarding_agent",
            "task_agent": "task_agent",
            "calendar_agent": "calendar_agent",
            "adaptive_learning_agent": "adaptive_learning_agent",
            "human": "human",
            END: END,
        }
    )
    
    # Agents can handoff to each other or end
    graph.add_conditional_edges(
        "onboarding_agent",
        should_continue_after_agent,
        {
            "router": "router",
            "task_agent": "task_agent",
            "calendar_agent": "calendar_agent",
            "human": "human",
            END: END,
        }
    )
    
    graph.add_conditional_edges(
        "task_agent",
        should_continue_after_agent,
        {
            "calendar_agent": "calendar_agent",
            "router": "router",
            "human": "human",
            END: END,
        }
    )
    
    graph.add_conditional_edges(
        "calendar_agent",
        should_continue_after_agent,
        {
            "task_agent": "task_agent",
            "router": "router",
            "human": "human",
            END: END,
        }
    )
    
    graph.add_conditional_edges(
        "adaptive_learning_agent",
        should_continue_after_agent,
        {
            "router": "router",
            "human": "human",
            END: END,
        }
    )
    
    graph.add_conditional_edges(
        "human",
        should_continue_after_agent,
        {
            "router": "router",
            END: END,
        }
    )
    
    return graph


def compile_graph() -> Any:
    """
    Compile the graph with checkpointer for conversation memory.
    
    Returns:
        Compiled LangGraph application
    """
    graph = build_graph()
    app = graph.compile(checkpointer=checkpointer)
    return app


# Global graph instance (lazy initialization)
_app: Optional[Any] = None


def get_graph() -> Any:
    """
    Get or create the compiled LangGraph application.
    
    Returns:
        Compiled LangGraph application
    """
    global _app
    if _app is None:
        _app = compile_graph()
        logger.info("LangGraph compiled and ready")
    return _app


async def process_message(
    user_id: int,
    message: str,
    telegram_update: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a user message through the LangGraph multi-agent system.
    
    Args:
        user_id: Telegram user ID
        message: User's message text
        telegram_update: Serialized Telegram Update object (optional)
    
    Returns:
        Dictionary with response data:
        - messages: List of messages from agents
        - active_agent: Agent that processed the message
        - state: Final state after processing
        - error: Error message if any
    """
    try:
        # Get current conversation state from legacy system
        current_state = get_conversation_state(user_id)
        context_data = get_conversation_context(user_id).data
        
        # Create initial LangGraph state
        initial_state = create_initial_state(
            user_id=user_id,
            message=message,
            telegram_update=telegram_update,
            current_state=current_state
        )
        
        # Update state from existing context
        initial_state = update_state_from_context(
            initial_state,
            user_id,
            current_state,
            context_data
        )
        
        # Get graph
        app = get_graph()
        
        # Create config for this conversation thread
        config = {
            "configurable": {
                "thread_id": str(user_id)  # Use user_id as thread_id for conversation persistence
            }
        }
        
        # Invoke graph
        logger.info(f"LangGraph: Processing message for user {user_id}")
        result = await app.ainvoke(initial_state, config)
        
        # Extract response
        messages = result.get("messages", [])
        active_agent = result.get("active_agent")
        
        # Get last AI message if any
        ai_message = None
        if messages:
            for msg in reversed(messages):
                if hasattr(msg, 'content') and not isinstance(msg, type(messages[0])):  # Check if it's an AI message
                    ai_message = msg.content
                    break
                elif isinstance(msg, dict) and msg.get("role") == "assistant":
                    ai_message = msg.get("content")
                    break
        
        return {
            "messages": messages,
            "active_agent": active_agent,
            "state": result,
            "response": ai_message or "I received your message.",
            "error": result.get("error"),
        }
        
    except Exception as e:
        logger.error(f"LangGraph: Error processing message: {e}", exc_info=True)
        return {
            "messages": [],
            "active_agent": None,
            "state": {},
            "response": "I encountered an error processing your message. Please try again.",
            "error": str(e),
        }

