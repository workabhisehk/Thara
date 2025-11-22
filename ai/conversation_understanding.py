"""
AI-powered conversation understanding for natural language interactions.
Uses OpenAI to understand conversational context and respond appropriately.
"""
import logging
from typing import Dict, Any, Optional
from ai.langchain_setup import get_llm, get_fallback_llm
from langchain_core.messages import HumanMessage, SystemMessage
import json

logger = logging.getLogger(__name__)


CONVERSATION_UNDERSTANDING_PROMPT = """You are Thara, an AI productivity assistant. Your task is to understand what the user is saying in natural English and determine:

1. **Intent**: What does the user want to do?
   - add_task, show_tasks, update_task, complete_task, delete_task
   - schedule_task, view_calendar, query_calendar
   - ask_question, general_chat, provide_feedback
   - update_settings, view_insights, request_help

2. **Context**: What are they referring to? (tasks, calendar events, settings, etc.)

3. **Entities**: Extract relevant details (task titles, dates, priorities, etc.)

4. **Action Required**: What should you do with this information?

Respond in JSON format:
{{
    "intent": "intent_name",
    "confidence": 0.9,
    "entities": {{
        "task_title": "...",
        "priority": "...",
        "due_date": "...",
        "pillar": "...",
        "time": "...",
        "date": "..."
    }},
    "action": "create_task|show_tasks|respond|clarify",
    "needs_clarification": false,
    "clarification_question": null,
    "response_suggestion": "How to respond to the user conversationally"
}}

Be conversational and understanding. Extract meaning even from casual or incomplete statements.
Remember: You're Thara, and you should understand English naturally, not require robotic input formats.
"""


async def understand_conversation(
    user_message: str,
    conversation_history: list = None,
    current_state: str = None
) -> Dict[str, Any]:
    """
    Understand user's natural language message using AI.
    
    Args:
        user_message: User's message
        conversation_history: Recent conversation context (optional)
        current_state: Current conversation state (optional)
    
    Returns:
        Dictionary with intent, entities, and action suggestions
    """
    try:
        llm = get_llm()
        
        # Build context
        context_parts = []
        if current_state:
            context_parts.append(f"Current state: {current_state}")
        if conversation_history:
            context_parts.append(f"Recent conversation: {conversation_history[-3:]}")  # Last 3 messages
        
        context = "\n".join(context_parts) if context_parts else "No specific context"
        
        messages = [
            SystemMessage(content=CONVERSATION_UNDERSTANDING_PROMPT),
            HumanMessage(content=f"User message: {user_message}\n\nContext: {context}\n\nUnderstand and extract information:")
        ]
        
        response = llm.invoke(messages)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
            # Validate and normalize
            result = {
                "intent": result.get("intent", "general_chat"),
                "confidence": float(result.get("confidence", 0.7)),
                "entities": result.get("entities", {}),
                "action": result.get("action", "respond"),
                "needs_clarification": result.get("needs_clarification", False),
                "clarification_question": result.get("clarification_question"),
                "response_suggestion": result.get("response_suggestion", "")
            }
            
            logger.info(f"Understood conversation: intent={result['intent']}, confidence={result['confidence']}")
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from conversation understanding: {e}")
            logger.warning(f"Response was: {response_text[:200]}")
            
            # Fallback: basic intent detection
            return {
                "intent": "general_chat",
                "confidence": 0.5,
                "entities": {},
                "action": "respond",
                "needs_clarification": True,
                "clarification_question": "Could you clarify what you'd like me to do?",
                "response_suggestion": "I understand you're asking something. Could you help me understand better?"
            }
            
    except Exception as e:
        logger.error(f"Error understanding conversation: {e}", exc_info=True)
        
        # Fallback response
        return {
            "intent": "general_chat",
            "confidence": 0.3,
            "entities": {},
            "action": "respond",
            "needs_clarification": True,
            "clarification_question": None,
            "response_suggestion": "I'm having trouble understanding. Could you rephrase?",
            "error": str(e)
        }


async def generate_conversational_response(
    user_message: str,
    intent: str,
    entities: Dict[str, Any],
    conversation_context: Dict[str, Any] = None
) -> str:
    """
    Generate a conversational response using AI.
    
    Args:
        user_message: User's message
        intent: Detected intent
        entities: Extracted entities
        conversation_context: Additional context (tasks, calendar, etc.)
    
    Returns:
        Natural conversational response
    """
    try:
        llm = get_llm()
        
        context_str = ""
        if conversation_context:
            context_parts = []
            if conversation_context.get("tasks"):
                context_parts.append(f"User's tasks: {conversation_context['tasks']}")
            if conversation_context.get("calendar_events"):
                context_parts.append(f"Calendar: {conversation_context['calendar_events']}")
            if conversation_context.get("user_preferences"):
                context_parts.append(f"Preferences: {conversation_context['user_preferences']}")
            context_str = "\n".join(context_parts)
        
        prompt = f"""You are Thara, an AI productivity assistant. The user said: "{user_message}"

Intent: {intent}
Entities extracted: {entities}
Context: {context_str}

Generate a natural, conversational response. Be helpful, concise, and friendly. 
Don't be robotic - respond like you understand what they're saying.

If they want to create a task, acknowledge it and confirm details.
If they're asking a question, answer it naturally.
If they're being casual, match their tone (but stay professional).

Your response:"""
        
        messages = [
            SystemMessage(content="You are Thara, a helpful AI productivity assistant. Be conversational and natural."),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        return response_text.strip()
        
    except Exception as e:
        logger.error(f"Error generating conversational response: {e}")
        # Fallback
        return "I understand. Let me help you with that. Could you provide a bit more detail?"

