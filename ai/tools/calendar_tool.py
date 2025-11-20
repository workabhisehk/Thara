"""
LangChain tool for calendar operations.
"""
from langchain.tools import tool
from calendar.client import list_events, create_event
from database.connection import AsyncSessionLocal


@tool
async def get_calendar_events(user_id: int, days: int = 7) -> str:
    """Get calendar events for the next N days."""
    async with AsyncSessionLocal() as session:
        try:
            events = await list_events(session, user_id, max_results=20)
            if not events:
                return "No events found."
            
            result = "Upcoming events:\n"
            for event in events[:10]:
                result += f"- {event.get('summary')} at {event.get('start')}\n"
            return result
        except Exception as e:
            return f"Error getting events: {str(e)}"


@tool
async def create_calendar_event(
    user_id: int,
    title: str,
    start_time: str,
    end_time: str,
    description: str = ""
) -> str:
    """Create a calendar event."""
    from datetime import datetime
    
    async with AsyncSessionLocal() as session:
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            
            event = await create_event(
                session,
                user_id,
                title,
                start,
                end,
                description
            )
            return f"Event created: {event.get('summary')} at {event.get('start')}"
        except Exception as e:
            return f"Error creating event: {str(e)}"

