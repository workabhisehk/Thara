"""
Parlant agent setup for Thara productivity assistant.
Configures guidelines, journeys, and tools for reliable rule-following behavior.
"""
import logging
from typing import Optional, Dict, Any, Tuple
import parlant.sdk as p
from agents_parlant.tools import (
    get_user_tasks,
    create_user_task,
    get_calendar_events,
    create_calendar_event,
    get_user_info
)

logger = logging.getLogger(__name__)

# Global server instance (initialized per user session)
_parlant_server: Optional[p.Server] = None
_parlant_agents: Dict[int, p.Agent] = {}  # user_id -> agent
_parlant_customers: Dict[int, p.Customer] = {}  # user_id -> customer
_parlant_sessions: Dict[int, p.Session] = {}  # user_id -> session
_customer_to_user_id: Dict[str, int] = {}  # customer_id -> telegram user_id


async def get_or_create_session(user_id: int) -> p.Session:
    """
    Get or create a Parlant session for a user.
    Each user gets their own session with personalized context.
    
    Args:
        user_id: Telegram user ID
    
    Returns:
        Parlant Session instance
    """
    global _parlant_server, _parlant_agents, _parlant_customers, _parlant_sessions, _customer_to_user_id
    
    # Return existing session if available
    if user_id in _parlant_sessions:
        return _parlant_sessions[user_id]
    
    # Initialize server if needed
    if _parlant_server is None:
        # Ensure OPENAI_API_KEY is in environment for Parlant
        import os
        from config import settings
        if not os.getenv('OPENAI_API_KEY') and settings.openai_api_key:
            os.environ['OPENAI_API_KEY'] = settings.openai_api_key
            logger.info("Set OPENAI_API_KEY in environment for Parlant")
        
        try:
            _parlant_server = p.Server()
            await _parlant_server.__aenter__()
            logger.info("Parlant server initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Parlant server: {e}", exc_info=True)
            raise
    
    # Get or create agent (shared across all users, or per-user if needed)
    if user_id not in _parlant_agents:
        agent = await _parlant_server.create_agent(
            name=f"Thara-{user_id}",
            description=(
                "You are Thara, a helpful productivity assistant. "
                "You help users manage tasks, schedule calendar events, and stay organized. "
                "Be friendly, proactive, and always confirm actions before executing them. "
                "Use tools to get information when needed, and provide clear, actionable responses.\n\n"
                "**CRITICAL: CONVERSATION CONTINUITY**\n"
                "- You maintain conversation history and context across multiple messages\n"
                "- When a user responds to your question, it's continuing the current conversation\n"
                "- Extract ALL information from the conversation history before asking for more details\n"
                "- If you asked for task details and user provides them, combine all information and complete the action\n"
                "- Don't ask for information you already have from previous messages\n"
                "- When user says 'yes' or provides details, use them to complete the current task\n\n"
                "**IMPORTANT FORMATTING RULES:**\n"
                "- Always structure your responses with clear paragraphs (use double line breaks)\n"
                "- Break long responses into multiple paragraphs for readability\n"
                "- Use line breaks to separate different topics or ideas\n"
                "- Keep paragraphs concise (2-4 sentences each)\n"
                "- Use bullet points or numbered lists when listing multiple items\n"
                "- Format responses for easy reading on mobile devices"
            )
        )
        
        # Register tools
        await agent.create_tool(get_user_tasks)
        await agent.create_tool(create_user_task)
        await agent.create_tool(get_calendar_events)
        await agent.create_tool(create_calendar_event)
        await agent.create_tool(get_user_info)
        
        # Create guidelines for reliable behavior
        await _setup_guidelines(agent, user_id)
        
        _parlant_agents[user_id] = agent
        logger.info(f"Created Parlant agent for user {user_id}")
    
    agent = _parlant_agents[user_id]
    
    # Get or create customer
    if user_id not in _parlant_customers:
        # Get user name from database if available
        try:
            from database.connection import AsyncSessionLocal
            from database.models import User
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as session:
                stmt = select(User).where(User.telegram_id == user_id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()
                customer_name = db_user.preferred_name or db_user.first_name if db_user else f"User-{user_id}"
        except:
            customer_name = f"User-{user_id}"
        
        customer = await _parlant_server.create_customer(name=customer_name)
        _parlant_customers[user_id] = customer
        _customer_to_user_id[customer.id] = user_id  # Map customer ID to telegram user_id
        logger.info(f"Created Parlant customer for user {user_id} (customer_id: {customer.id})")
    
    customer = _parlant_customers[user_id]
    
    # Create session for this customer
    session = await agent.create_session(
        customer_id=customer.id,
        title=f"Thara Conversation - User {user_id}"
    )
    
    _parlant_sessions[user_id] = session
    logger.info(f"Created Parlant session for user {user_id}")
    
    return session


def _format_response(text: str) -> str:
    """
    Format response text with proper paragraph breaks.
    
    Ensures responses are well-structured with clear paragraphs.
    """
    if not text:
        return text
    
    # Split by common sentence endings followed by space
    import re
    
    # First, ensure double line breaks are preserved
    text = re.sub(r'\n\n+', '\n\n', text)  # Normalize multiple line breaks
    
    # If text is very long without paragraph breaks, try to add them
    # Look for patterns like ". " followed by capital letter (new sentence)
    # But don't break if it's already well-formatted
    
    # Count existing paragraph breaks
    paragraph_breaks = text.count('\n\n')
    total_length = len(text)
    
    # If text is long (>200 chars) and has few paragraph breaks, try to add structure
    if total_length > 200 and paragraph_breaks < 2:
        # Try to break at sentence boundaries after periods/full stops
        # But be careful not to break URLs, decimals, etc.
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        if len(sentences) > 3:
            # Group sentences into paragraphs (2-3 sentences per paragraph)
            paragraphs = []
            current_para = []
            
            for sentence in sentences:
                current_para.append(sentence.strip())
                # Start new paragraph every 2-3 sentences
                if len(current_para) >= 2 and len(current_para) % 2 == 0:
                    paragraphs.append(' '.join(current_para))
                    current_para = []
            
            if current_para:
                paragraphs.append(' '.join(current_para))
            
            if len(paragraphs) > 1:
                text = '\n\n'.join(paragraphs)
    
    # Clean up any excessive whitespace
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space
    text = re.sub(r'\n{3,}', '\n\n', text)  # More than 2 newlines to 2
    
    return text.strip()


async def _setup_guidelines(agent: p.Agent, user_id: int) -> None:
    """Setup guidelines for the agent."""
    
    # Task management guidelines
    await agent.create_guideline(
        condition="User asks about tasks, wants to see tasks, or asks what tasks they have",
        action="Use get_user_tasks tool to retrieve and display their tasks in a friendly, organized format",
        tools=[get_user_tasks]
    )
    
    await agent.create_guideline(
        condition="User wants to add a task, create a task, or mentions a new task",
        action=(
            "Extract task details (title, description, priority, due date, pillar) from the CURRENT message AND previous conversation history. "
            "Review the conversation to gather ALL available information before asking for more details.\n\n"
            "If you have enough information to create the task, use create_user_task tool immediately. "
            "If information is missing, ask for ONLY the missing pieces.\n\n"
            "**CRITICAL:** When user responds to your questions (like 'yes', 'monday morning', '10am'), "
            "combine that information with what you already know from previous messages and complete the task creation. "
            "Don't ask for information you already have. Don't restart the conversation."
        ),
        tools=[create_user_task]
    )
    
    await agent.create_guideline(
        condition="User responds with 'yes', 'no', a time, a date, or other details after you asked a question",
        action=(
            "This is a CONTINUATION of the previous conversation. "
            "Review the conversation history to understand what you were asking about. "
            "Extract the information from their response and combine it with information from previous messages. "
            "If you were in the middle of creating a task or scheduling something, use the new information to complete that action. "
            "Don't ask for information you already have. Don't start a new conversation topic."
        )
    )
    
    await agent.create_guideline(
        condition="User provides partial information (like just a time '10am' or just a date 'monday')",
        action=(
            "This is likely continuing a previous conversation. "
            "Check conversation history to see what you were discussing. "
            "If you were creating a task and asked for details, combine this new information with what you already know. "
            "For example, if previous message mentioned 'check with Prof. Caroline' and now user says '10am', "
            "create a task titled 'Check with Prof. Caroline' with due date/time from the conversation context."
        ),
        tools=[create_user_task]
    )
    
    await agent.create_guideline(
        condition="User asks about their calendar, upcoming events, schedule, or if you can access their calendar",
        action=(
            "Use get_calendar_events tool to retrieve and display their calendar events.\n\n"
            "If the calendar is not connected, the tool will provide instructions on how to connect it. "
            "Always explain that you CAN access their calendar once it's connected via Google Calendar OAuth.\n\n"
            "When displaying events, format them clearly:\n"
            "- Use line breaks between different events\n"
            "- Group events by date when possible\n"
            "- Show dates, times, and locations clearly\n\n"
            "Structure your response in clear paragraphs with proper formatting."
        ),
        tools=[get_calendar_events]
    )
    
    await agent.create_guideline(
        condition="User wants to schedule something, add a calendar event, or create an event",
        action=(
            "Extract event details (title, start time, end time, location, description) from the message. "
            "Use create_calendar_event tool to create the event. Always confirm the event was created. "
            "If time information is unclear, ask for clarification."
        ),
        tools=[create_calendar_event]
    )
    
    await agent.create_guideline(
        condition="User asks about themselves, their preferences, or their account",
        action="Use get_user_info tool to retrieve their information and provide a helpful summary",
        tools=[get_user_info]
    )
    
    # Response formatting guideline
    await agent.create_guideline(
        condition="Always when responding to any message",
        action=(
            "Structure your response with clear paragraphs. Use double line breaks (\\n\\n) to separate paragraphs. "
            "Break long responses into multiple paragraphs (2-4 sentences each). "
            "Use line breaks to separate different topics or ideas. "
            "Keep responses well-formatted and easy to read on mobile devices."
        )
    )
    
    # General conversation guidelines
    await agent.create_guideline(
        condition="User greets or says hello",
        action=(
            "Respond warmly and offer to help with tasks, calendar, or productivity needs. "
            "Be friendly and approachable.\n\n"
            "Structure your response in clear paragraphs with proper line breaks."
        )
    )
    
    await agent.create_guideline(
        condition="User asks for help or doesn't know what to do",
        action=(
            "Explain that you can help with: "
            "- Managing tasks (view, create, update) "
            "- Calendar events (view, schedule) "
            "- Productivity insights "
            "Ask what they'd like help with."
        )
    )
    
    await agent.create_guideline(
        condition="User's request is unclear or ambiguous",
        action=(
            "First, review the conversation history to see if this is continuing a previous topic. "
            "If it's a continuation, use context from previous messages to understand the request. "
            "Only ask clarifying questions if you truly don't have enough information. "
            "Be specific about what information you need, but don't ask for information you already have."
        )
    )
    
    await agent.create_guideline(
        condition="Always before responding to any message",
        action=(
            "1. Review the conversation history to understand the full context\n"
            "2. Check if this message is continuing a previous conversation\n"
            "3. Extract ALL available information from the conversation (current + previous messages)\n"
            "4. If you have enough information to complete an action, do it immediately\n"
            "5. Only ask for missing information if absolutely necessary\n"
            "6. Don't restart conversations or ask for information you already have"
        )
    )
    
    await agent.create_guideline(
        condition="User thanks you or expresses appreciation",
        action="Respond graciously and offer continued assistance. Be warm and genuine."
    )
    
    # Error handling guidelines
    await agent.create_guideline(
        condition="A tool returns an error or user information is missing",
        action=(
            "Acknowledge the issue clearly. If it's a missing setup (like calendar not connected), "
            "explain what needs to be done. If it's a validation error, explain what was wrong and how to fix it. "
            "Always provide next steps."
        )
    )
    
    await agent.create_guideline(
        condition="User asks if you can access their calendar or if calendar integration works",
        action=(
            "Explain that you CAN access their Google Calendar once it's connected.\n\n"
            "Use get_calendar_events tool to check connection status.\n\n"
            "If not connected, guide them to use /calendar command or provide the OAuth link from the tool response. "
            "Be clear that calendar access requires OAuth authorization for security.\n\n"
            "Format your response in clear paragraphs for easy reading."
        ),
        tools=[get_calendar_events]
    )


async def process_message(user_id: int, message: str) -> str:
    """
    Process a user message through Parlant agent using sessions.
    
    Args:
        user_id: Telegram user ID
        message: User's message text
    
    Returns:
        Agent's response text
    """
    import asyncio
    
    try:
        # Get or create session
        session = await get_or_create_session(user_id)
        
        # Store user_id in session metadata for tools to access
        # We'll pass it through the ToolContext
        # First, we need to ensure tools can access user_id
        # Parlant's ToolContext should have access to customer/session info
        
        # Get recent conversation history to provide context
        # This helps the agent understand conversation continuity
        try:
            recent_events = await session.list_events()
            recent_messages = [
                event for event in recent_events[-10:]  # Last 10 events
                if event.kind == p.EventKind.MESSAGE
            ]
            
            # Build context summary if there's conversation history
            if len(recent_messages) > 1:
                context_summary = "Previous conversation context:\n"
                for event in recent_messages[-5:]:  # Last 5 messages for context
                    speaker = "User" if event.source == p.EventSource.CUSTOMER else "You"
                    msg_text = event.data.get('message', '')[:100]  # First 100 chars
                    if msg_text:
                        context_summary += f"- {speaker}: {msg_text}\n"
                
                # Add context to the message
                message_with_context = f"{context_summary}\n\nCurrent message: {message}"
            else:
                message_with_context = message
        except Exception as e:
            logger.debug(f"Could not build context summary: {e}")
            message_with_context = message
        
        # Post customer message to session
        await session.post_message(
            message=message_with_context,
            source=p.EventSource.CUSTOMER
        )
        
        # Wait for agent to process and respond
        # Parlant processes messages asynchronously
        await asyncio.sleep(1.5)  # Give agent slightly more time to process with context
        
        # Retrieve events to get agent response
        events = await session.list_events()
        
        # Find the most recent agent message
        agent_messages = [
            event for event in events
            if event.source == p.EventSource.AI_AGENT and event.kind == p.EventKind.MESSAGE
        ]
        
        if agent_messages:
            # Get the latest agent message
            latest_message = agent_messages[-1]
            response_text = latest_message.data.get('message', '')
            
            if response_text:
                # Format response with proper paragraph breaks
                formatted_response = _format_response(response_text)
                return formatted_response
        
        # If no agent message found, return a default response
        logger.warning(f"No agent response found for user {user_id}")
        return "I received your message. Let me process that for you..."
        
    except Exception as e:
        logger.error(f"Error processing message with Parlant: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"I encountered an error processing your message. Please try again or use /help for assistance."


async def cleanup():
    """Cleanup Parlant server, agents, customers, and sessions."""
    global _parlant_server, _parlant_agents, _parlant_customers, _parlant_sessions, _customer_to_user_id
    
    if _parlant_server:
        try:
            await _parlant_server.__aexit__(None, None, None)
        except Exception as e:
            logger.warning(f"Error cleaning up Parlant server: {e}")
    
    _parlant_agents.clear()
    _parlant_customers.clear()
    _parlant_sessions.clear()
    _customer_to_user_id.clear()
    _parlant_server = None

