"""
Inline keyboards for Telegram bot interactions.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import PillarType, TaskPriority


def get_pillar_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for pillar selection."""
    keyboard = [
        [
            InlineKeyboardButton("Work", callback_data=f"pillar_{PillarType.WORK.value}"),
            InlineKeyboardButton("Education", callback_data=f"pillar_{PillarType.EDUCATION.value}"),
        ],
        [
            InlineKeyboardButton("Projects", callback_data=f"pillar_{PillarType.PROJECTS.value}"),
            InlineKeyboardButton("Personal", callback_data=f"pillar_{PillarType.PERSONAL.value}"),
        ],
        [
            InlineKeyboardButton("Other", callback_data=f"pillar_{PillarType.OTHER.value}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_priority_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for priority selection."""
    keyboard = [
        [
            InlineKeyboardButton("High", callback_data=f"priority_{TaskPriority.HIGH.value}"),
            InlineKeyboardButton("Medium", callback_data=f"priority_{TaskPriority.MEDIUM.value}"),
            InlineKeyboardButton("Low", callback_data=f"priority_{TaskPriority.LOW.value}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Get yes/no keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="yes"),
            InlineKeyboardButton("No", callback_data="no"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Get confirmation keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data="confirm"),
            InlineKeyboardButton("Cancel", callback_data="cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_task_actions_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for task actions."""
    keyboard = [
        [
            InlineKeyboardButton("Complete", callback_data=f"task_complete_{task_id}"),
            InlineKeyboardButton("Edit", callback_data=f"task_edit_{task_id}"),
        ],
        [
            InlineKeyboardButton("Schedule", callback_data=f"task_schedule_{task_id}"),
            InlineKeyboardButton("Delete", callback_data=f"task_delete_{task_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

