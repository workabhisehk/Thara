"""
Batch task operations.
"""
import logging
from typing import List, Dict, Any
from tasks.service import create_task
from database.connection import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def process_batch_tasks(
    user_id: int,
    tasks_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Process multiple tasks in batch.
    
    Args:
        user_id: User ID
        tasks_data: List of task dictionaries
    
    Returns:
        Dictionary with results
    """
    results = {
        "success": [],
        "failed": []
    }
    
    async with AsyncSessionLocal() as session:
        for task_data in tasks_data:
            try:
                task = await create_task(
                    session,
                    user_id,
                    title=task_data.get("title", ""),
                    description=task_data.get("description"),
                    pillar=task_data.get("pillar"),
                    priority=task_data.get("priority"),
                    due_date=task_data.get("due_date"),
                    estimated_duration=task_data.get("estimated_duration")
                )
                results["success"].append({
                    "task_id": task.id,
                    "title": task.title
                })
            except Exception as e:
                logger.error(f"Error creating task in batch: {e}")
                results["failed"].append({
                    "title": task_data.get("title", "Unknown"),
                    "error": str(e)
                })
        
        await session.commit()
    
    return results

