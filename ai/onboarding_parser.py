"""
AI-powered natural language parser for onboarding.
Uses OpenAI to understand conversational input and extract structured information.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from ai.langchain_setup import get_llm
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


ONBOARDING_PARSER_PROMPT = """You are Thara, an AI productivity assistant helping users during onboarding.

Your task is to understand what the user is saying and extract relevant information from their natural language responses.

The user might be providing:
1. **Categories/Pillars**: They might mention categories like "work", "education", "projects", "personal", or custom categories
2. **Work Hours**: They might describe their work schedule in any format (e.g., "9 AM to 5 PM", "Monday-Friday 9-5", "MWF 9am-4:45pm", or complex schedules with travel time)
3. **Timezone**: They might mention their timezone
4. **Other information**: Any other relevant onboarding details

Extract the information and respond in JSON format:
{{
    "pillars": ["work", "education", ...],  // List of mentioned categories/pillars (empty if none)
    "work_hours": {{
        "days": ["monday", "wednesday", ...],  // Days of week (empty if not mentioned)
        "start_time": "09:00",  // Start time in 24h format (HH:MM) or null
        "end_time": "17:00",  // End time in 24h format (HH:MM) or null
        "notes": "Travel time 2 hours"  // Any additional notes (travel time, classes, etc.)
    }},
    "timezone": "America/New_York",  // Timezone if mentioned, null otherwise
    "confidence": 0.9,  // Confidence score 0-1
    "response_type": "work_hours|pillars|timezone|general"  // What the user is providing
}}

Examples:

User: "Monday, wednesday, thursday and friday from 9:00 AM to 4:45 PM are my work hours. But, it takes 2 hours to travel to work and back home from work after work. I have classes on tuesday 4:00 PM to 7:00 PM"
Response:
{{
    "pillars": [],
    "work_hours": {{
        "days": ["monday", "wednesday", "thursday", "friday"],
        "start_time": "09:00",
        "end_time": "16:45",
        "notes": "Travel time 2 hours each way. Classes on Tuesday 4:00 PM to 7:00 PM"
    }},
    "timezone": null,
    "confidence": 0.95,
    "response_type": "work_hours"
}}

User: "I also have work pillar"
Response:
{{
    "pillars": ["work"],
    "work_hours": {{}},
    "timezone": null,
    "confidence": 0.9,
    "response_type": "pillars"
}}

User: "9 AM to 5 PM"
Response:
{{
    "pillars": [],
    "work_hours": {{
        "days": [],
        "start_time": "09:00",
        "end_time": "17:00",
        "notes": ""
    }},
    "timezone": null,
    "confidence": 0.95,
    "response_type": "work_hours"
}}

Be conversational and understanding. Extract all relevant information even if the user is not perfectly clear.
"""


async def parse_onboarding_message(user_message: str, current_step: str = None) -> Dict[str, Any]:
    """
    Parse natural language onboarding message using AI.
    
    Args:
        user_message: User's natural language message
        current_step: Current onboarding step (optional, for context)
    
    Returns:
        Dictionary with extracted information
    """
    try:
        llm = get_llm()
        
        # Add current step context to prompt
        context_prompt = ONBOARDING_PARSER_PROMPT
        if current_step:
            context_prompt += f"\n\nCurrent onboarding step: {current_step}\nExtract information relevant to this step."
        
        messages = [
            SystemMessage(content=context_prompt),
            HumanMessage(content=f"User message: {user_message}\n\nExtract information from this message:")
        ]
        
        response = llm.invoke(messages)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Try to parse JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
            # Validate and normalize result
            result = {
                "pillars": result.get("pillars", []),
                "work_hours": result.get("work_hours", {}),
                "timezone": result.get("timezone"),
                "confidence": float(result.get("confidence", 0.7)),
                "response_type": result.get("response_type", "general")
            }
            
            logger.info(f"Parsed onboarding message: {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from AI response: {e}")
            logger.warning(f"Response was: {response_text[:200]}")
            # Fallback: try to extract basic info
            return {
                "pillars": [],
                "work_hours": {},
                "timezone": None,
                "confidence": 0.3,
                "response_type": "general",
                "raw_response": response_text
            }
            
    except Exception as e:
        logger.error(f"Error parsing onboarding message with AI: {e}", exc_info=True)
        return {
            "pillars": [],
            "work_hours": {},
            "timezone": None,
            "confidence": 0.0,
            "response_type": "general",
            "error": str(e)
        }


def normalize_time_to_24h(time_str: str) -> Optional[str]:
    """
    Normalize time string to 24-hour format (HH:MM).
    
    Args:
        time_str: Time in any format (e.g., "9 AM", "09:00", "4:45 PM")
    
    Returns:
        Time in 24-hour format (HH:MM) or None
    """
    import re
    
    if not time_str:
        return None
    
    time_str = time_str.strip().upper()
    
    # Pattern 1: "9 AM" or "9:45 PM"
    match = re.search(r'(\d+):?(\d+)?\s*(AM|PM)', time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3)
        
        if period == "PM" and hour != 12:
            hour += 12
        elif period == "AM" and hour == 12:
            hour = 0
        
        return f"{hour:02d}:{minute:02d}"
    
    # Pattern 2: Already in 24h format "09:00" or "9:00"
    match = re.search(r'(\d+):(\d+)', time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        if 0 <= hour < 24 and 0 <= minute < 60:
            return f"{hour:02d}:{minute:02d}"
    
    # Pattern 3: Just hour "9" (assume AM)
    match = re.search(r'^\d+$', time_str)
    if match:
        hour = int(match.group(0))
        if 0 <= hour < 24:
            return f"{hour:02d}:00"
    
    return None


def normalize_days_of_week(days: List[str]) -> List[str]:
    """
    Normalize day names to lowercase standard format.
    
    Args:
        days: List of day names in any format
    
    Returns:
        List of normalized day names
    """
    day_mapping = {
        "monday": "monday", "mon": "monday",
        "tuesday": "tuesday", "tue": "tuesday", "tues": "tuesday",
        "wednesday": "wednesday", "wed": "wednesday",
        "thursday": "thursday", "thu": "thursday", "thur": "thursday",
        "friday": "friday", "fri": "friday",
        "saturday": "saturday", "sat": "saturday",
        "sunday": "sunday", "sun": "sunday"
    }
    
    normalized = []
    for day in days:
        day_lower = day.lower().strip()
        if day_lower in day_mapping:
            normalized_day = day_mapping[day_lower]
            if normalized_day not in normalized:
                normalized.append(normalized_day)
    
    return normalized

