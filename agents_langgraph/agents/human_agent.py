"""
Human Agent: Handles clarification requests and user input collection.
Acts as an interrupt point for collecting user input when agents need clarification.
"""
import logging
from typing import Literal
from langgraph.types import Command
from agents_langgraph.state import AgentState
, interrupt

logger = logging.getLogger(__name__)


async def human_agent(state: AgentState) -> Command[Literal["router_agent", "human", "__end__"]]:
    """
    Human agent - handles clarification and user input collection.
    
    Uses LangGraph's interrupt mechanism to:
    - Collect user input when agents need clarification
    - Resume conversation after clarification
    - Guide users through complex flows
    
    Can handoff to:
    - router_agent: After clarification, re-route to appropriate agent
    - __end__: Complete clarification response
    """
    try:
        user_id = state.get("user_id")
        clarification_message = state.get("clarification_message")
        needs_clarification = state.get("needs_clarification", False)
        messages = state.get("messages", [])
        
        logger.info(f"HumanAgent: Processing for user {user_id}, needs_clarification: {needs_clarification}")
        
        if needs_clarification and clarification_message:
            # Request clarification using interrupt
            user_input = interrupt(value=clarification_message)
            
            # Add user's clarification to messages
            from langchain_core.messages import HumanMessage
            clarification_msg = HumanMessage(content=user_input)
            
            # Route back to router with clarification
            return Command(
                goto="router_agent",
                update={
                    "messages": [clarification_msg],
                    "needs_clarification": False,
                    "clarification_message": None,
                    "active_agent": "router_agent"
                }
            )
        
        # No clarification needed, end
        return Command(goto="__end__")
        
    except Exception as e:
        logger.error(f"HumanAgent: Error: {e}", exc_info=True)
        return Command(
            goto="__end__",
            update={"error": str(e)}
        )

