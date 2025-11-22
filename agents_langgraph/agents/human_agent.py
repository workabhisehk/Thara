"""
Human Agent: Handles clarification requests and user input collection.
Acts as an interrupt point for collecting user input when agents need clarification.
"""
import logging
from typing import Literal
from langgraph.types import Command
from agents_langgraph.state import AgentState

# Note: interrupt is typically used in LangGraph checkpoints, not in agent functions
# For Telegram bot, we handle interrupts through the integration layer

logger = logging.getLogger(__name__)


async def human_agent(state: AgentState) -> Command[Literal["router", "human", "__end__"]]:
    """
    Human agent - handles clarification and user input collection.
    
    Uses LangGraph's interrupt mechanism to:
    - Collect user input when agents need clarification
    - Resume conversation after clarification
    - Guide users through complex flows
    
    Can handoff to:
    - router: After clarification, re-route to appropriate agent
    - __end__: Complete clarification response
    """
    try:
        user_id = state.get("user_id")
        clarification_message = state.get("clarification_message")
        needs_clarification = state.get("needs_clarification", False)
        messages = state.get("messages", [])
        
        logger.info(f"HumanAgent: Processing for user {user_id}, needs_clarification: {needs_clarification}")
        
        if needs_clarification and clarification_message:
            # For Telegram bot, clarification is handled in the integration layer
            # This agent just sets up the clarification request in state
            # The integration layer will send the message and wait for user response
            
            # Update state to indicate clarification needed
            return Command(
                goto="__end__",
                update={
                    "needs_clarification": True,
                    "clarification_message": clarification_message,
                    "active_agent": "human"
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

