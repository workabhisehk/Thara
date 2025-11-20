"""
LangChain tool for task operations.
"""
from langchain.tools import tool
from tasks.service import get_tasks, create_task
from database.connection import AsyncSessionLocal


@tool
async def get_user_tasks(user_id: int, status: str = "active") -> str:
    """Get user's tasks."""
    async with AsyncSessionLocal() as session:
        try:
            tasks = await get_tasks(session, user_id, status=status)
            if not tasks:
                return "No tasks found."
            
            result = "Your tasks:\n"
            for task in tasks[:10]:
                result += f"- {task.title} ({task.priority.value}, {task.status.value})\n"
            return result
        except Exception as e:
            return f"Error getting tasks: {str(e)}"


@tool
async def add_task(
    user_id: int,
    title: str,
    pillar: str = "other",
    priority: str = "medium"
) -> str:
    """Add a new task."""
    async with AsyncSessionLocal() as session:
        try:
            task = await create_task(
                session,
                user_id,
                title,
                pillar=pillar,
                priority=priority
            )
            return f"Task created: {task.title}"
        except Exception as e:
            return f"Error creating task: {str(e)}"

