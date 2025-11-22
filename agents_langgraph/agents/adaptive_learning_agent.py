"""
Adaptive Learning Agent: Handles insights, patterns, and adaptive learning features.
Manages pattern detection, learning from corrections, automatic flow suggestions, and behavior adaptation.
"""
import logging
from typing import Literal
from langgraph.types import Command
from agents_langgraph.state import AgentState


logger = logging.getLogger(__name__)


async def adaptive_learning_agent(state: AgentState) -> Command[Literal["adaptive_learning_agent", "router", "human", "__end__"]]:
    """
    Adaptive Learning agent - handles insights and learning features.
    
    Manages:
    - Pattern detection and insights
    - Learning from user corrections
    - Automatic flow suggestions
    - Behavior adaptation
    - Feedback processing
    - Analytics and reports
    
    Can handoff to:
    - router: General query or redirect
    - human: Needs clarification
    - __end__: Complete learning operation
    """
    try:
        user_id = state.get("user_id")
        intent = state.get("intent")
        entities = state.get("entities", {})
        messages = state.get("messages", [])
        
        if not messages:
            logger.warning(f"AdaptiveLearningAgent: No messages for user {user_id}")
            return Command(goto="__end__")
        
        last_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
        
        logger.info(f"AdaptiveLearningAgent: Processing for user {user_id}, intent: {intent}")
        
        # Map intents to learning operations
        learning_operations = {
            "insights": "view_insights",
            "patterns": "view_patterns",
            "analytics": "view_analytics",
            "learn": "view_learning",
            "feedback": "process_feedback",
            "correction": "learn_from_correction",
        }
        
        operation = learning_operations.get(intent, "view_insights")
        
        # Store learning operation in agent data
        state["agent_data"]["adaptive_learning"] = {
            "operation": operation,
            "intent": intent,
            "entities": entities,
            "message": last_message
        }
        
        # Process based on operation
        if operation == "process_feedback":
            logger.info(f"AdaptiveLearningAgent: Processing feedback")
            # Feedback processing will be handled by existing feedback handler
            return Command(
                goto="__end__",
                update={
                    "active_agent": "adaptive_learning_agent",
                    "agent_data": state["agent_data"]
                }
            )
        
        if operation == "learn_from_correction":
            logger.info(f"AdaptiveLearningAgent: Learning from correction")
            # Correction learning will be handled by existing adaptive learning handler
            return Command(
                goto="__end__",
                update={
                    "active_agent": "adaptive_learning_agent",
                    "agent_data": state["agent_data"]
                }
            )
        
        # Default: view insights
        logger.info(f"AdaptiveLearningAgent: Viewing insights/patterns")
        # Insights viewing will be handled by existing insights handler
        return Command(
            goto="__end__",
            update={
                "active_agent": "adaptive_learning_agent",
                "agent_data": state["agent_data"]
            }
        )
        
    except Exception as e:
        logger.error(f"AdaptiveLearningAgent: Error: {e}", exc_info=True)
        return Command(
            goto="human",
            update={
                "error": str(e),
                "clarification_message": "I encountered an error processing your insights request. Please try again.",
                "active_agent": "human"
            }
        )

