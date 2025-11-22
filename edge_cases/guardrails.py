"""
Guardrails implementation according to AGENT_PERSONA_AND_EVALS.md
Enforces behavioral guardrails for the AI agent.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# Guardrails configuration
MIN_CONFIDENCE_THRESHOLD = 0.7  # Only suggest actions when confidence >70%
MAX_UNSOLICITED_MESSAGES_PER_DAY = 3  # Never send more than 3 unsolicited messages per day
MIN_CONFIRMATION_ACTIONS = [
    "create_calendar_event",
    "modify_calendar_event",
    "delete_calendar_event",
    "execute_automatic_flow",
    "change_task_priority",  # Unless explicitly allowed
    "delete_task",
]


async def check_confirmation_required(action_type: str) -> bool:
    """
    Check if an action requires user confirmation.
    According to AGENT_PERSONA_AND_EVALS.md - User Autonomy guardrails.
    
    Args:
        action_type: Type of action to check
    
    Returns:
        True if confirmation is required, False otherwise
    """
    return action_type in MIN_CONFIRMATION_ACTIONS


async def check_confidence_threshold(confidence: float) -> bool:
    """
    Check if confidence meets the minimum threshold for suggestions.
    According to AGENT_PERSONA_AND_EVALS.md - Suggestion Quality guardrails.
    
    Args:
        confidence: Confidence score (0.0-1.0)
    
    Returns:
        True if confidence meets threshold, False otherwise
    """
    return confidence >= MIN_CONFIDENCE_THRESHOLD


async def check_rate_limit(
    session: AsyncSession,
    user_id: int,
    message_type: str = "unsolicited"
) -> bool:
    """
    Check if user has exceeded rate limits for proactive messages.
    According to AGENT_PERSONA_AND_EVALS.md - Frequency & Timing guardrails.
    
    Args:
        session: Database session
        user_id: User ID
        message_type: Type of message ("unsolicited", "check_in", "reminder")
    
    Returns:
        True if rate limit not exceeded, False if exceeded
    """
    if message_type != "unsolicited":
        # Check-ins and reminders have separate limits
        return True
    
    # Count unsolicited messages sent today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # TODO: Add message tracking table to track unsolicited messages
    # For now, check conversation history for bot messages today
    from database.models import Conversation
    
    stmt = select(func.count(Conversation.id)).where(
        Conversation.user_id == user_id,
        Conversation.is_from_user == False,  # Bot messages
        Conversation.created_at >= today_start
    )
    
    result = await session.execute(stmt)
    count = result.scalar_one() or 0
    
    if count >= MAX_UNSOLICITED_MESSAGES_PER_DAY:
        logger.info(
            f"Rate limit exceeded for user {user_id}: {count} unsolicited messages today"
        )
        return False
    
    return True


async def check_user_autonomy(
    action_type: str,
    requires_confirmation: bool = None
) -> Dict[str, Any]:
    """
    Check user autonomy guardrails before taking actions.
    According to AGENT_PERSONA_AND_EVALS.md - User Autonomy guardrails.
    
    Args:
        action_type: Type of action
        requires_confirmation: Whether confirmation is already required (optional)
    
    Returns:
        Dictionary with:
        {
            "allowed": bool,
            "requires_confirmation": bool,
            "reason": str (if not allowed)
        }
    """
    # Check if confirmation is required
    if requires_confirmation is None:
        requires_confirmation = await check_confirmation_required(action_type)
    
    return {
        "allowed": True,  # Always allowed, but may require confirmation
        "requires_confirmation": requires_confirmation,
        "reason": None
    }


async def check_privacy_guardrails(
    user_id: int,
    data_type: str,
    action: str
) -> bool:
    """
    Check privacy guardrails before data operations.
    According to AGENT_PERSONA_AND_EVALS.md - Privacy & Data Protection guardrails.
    
    Args:
        user_id: User ID
        data_type: Type of data ("calendar", "task", "conversation", etc.)
        action: Action to perform ("share", "modify", "delete", etc.)
    
    Returns:
        True if action is allowed, False otherwise
    """
    # Privacy guardrails:
    # - Never share user data with external parties (unless explicitly allowed)
    # - Always ask for explicit confirmation before calendar modifications
    
    if data_type == "calendar" and action in ["modify", "delete", "create"]:
        # Calendar modifications always require explicit confirmation
        return False  # Not allowed without confirmation
    
    if action == "share" and data_type in ["calendar", "task", "conversation"]:
        # Never share user data externally
        logger.warning(f"Privacy guardrail: Sharing {data_type} not allowed")
        return False
    
    return True


async def check_work_hours(user_id: int, session: AsyncSession = None) -> bool:
    """
    Check if current time is within user's work hours.
    According to AGENT_PERSONA_AND_EVALS.md - Frequency & Timing guardrails.
    
    Args:
        user_id: User ID
        session: Database session (optional)
    
    Returns:
        True if within work hours, False otherwise
    """
    if session is None:
        async with AsyncSessionLocal() as session:
            return await check_work_hours(user_id, session)
    
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        return False
    
    now = datetime.utcnow()
    current_hour = now.hour
    
    # Check if within work hours
    return user.work_start_hour <= current_hour < user.work_end_hour


def format_user_friendly_error(
    error_type: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format user-friendly error messages following agent persona.
    According to AGENT_PERSONA_AND_EVALS.md - Error Handling guardrails.
    
    Args:
        error_type: Type of error
        error_message: Technical error message
        context: Additional context
    
    Returns:
        User-friendly error message
    """
    context = context or {}
    
    # Base user-friendly messages
    error_templates = {
        "database_error": (
            "I'm having trouble accessing the database right now. "
            "Please try again in a moment. If the problem persists, let me know."
        ),
        "dependency_error": (
            "A required system dependency is missing. "
            "Please contact support or check your installation."
        ),
        "llm_error": (
            "I'm having trouble processing your request with AI right now. "
            "Please try again, or use a command like /tasks to continue."
        ),
        "calendar_error": (
            "I couldn't access your calendar. Please check your connection "
            "or try again later."
        ),
        "validation_error": (
            "I couldn't process that input. {details} "
            "Please try again with a different format."
        ),
        "rate_limit": (
            "I've reached the limit for proactive messages today. "
            "I'll check in with you tomorrow!"
        ),
        "confirmation_required": (
            "This action requires confirmation. Please confirm to proceed."
        ),
        "low_confidence": (
            "I'm not certain about that request. Could you provide more details?"
        ),
    }
    
    # Get template or default
    template = error_templates.get(error_type, error_templates.get("validation_error"))
    
    # Format with context
    details = context.get("details", "")
    if details:
        return template.format(details=details)
    
    return template


async def log_guardrail_enforcement(
    session: AsyncSession,
    user_id: int,
    guardrail_type: str,
    action: str,
    enforced: bool,
    reason: Optional[str] = None
) -> None:
    """
    Log guardrail enforcement for monitoring and analytics.
    
    Args:
        session: Database session
        user_id: User ID
        guardrail_type: Type of guardrail enforced
        action: Action that was checked
        enforced: Whether guardrail was enforced (blocked)
        reason: Reason for enforcement (if enforced)
    """
    # TODO: Create guardrail_logs table for tracking
    # For now, just log
    logger.info(
        f"Guardrail enforcement: user={user_id}, type={guardrail_type}, "
        f"action={action}, enforced={enforced}, reason={reason}"
    )

