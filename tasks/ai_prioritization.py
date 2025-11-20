"""
AI-driven task prioritization using multiple factors.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from database.models import Task, TaskStatus, TaskPriority
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ai.langchain_setup import get_llm
from memory.pattern_learning import get_user_habits
from memory.context_retrieval import get_context_for_ai

logger = logging.getLogger(__name__)


async def ai_prioritize_tasks(
    session: AsyncSession,
    user_id: int,
    tasks: List[Task]
) -> List[Dict[str, Any]]:
    """
    Use AI to intelligently prioritize tasks based on multiple factors.
    
    Factors considered:
    - Deadline proximity
    - Estimated duration vs time available
    - Task dependencies
    - User's historical patterns
    - Current workload
    - Strategic importance (pillar)
    - Energy/time of day patterns
    
    Args:
        session: Database session
        user_id: User ID
        tasks: List of tasks to prioritize
    
    Returns:
        List of tasks with AI-assigned priority scores and reasoning
    """
    if not tasks:
        return []
    
    # Get user habits and patterns
    habits = await get_user_habits(session, user_id)
    
    # Get context
    context = await get_context_for_ai(session, user_id, "prioritize tasks")
    
    # Build prompt for AI prioritization
    tasks_info = []
    for task in tasks:
        time_until_deadline = None
        if task.due_date:
            time_until_deadline = (task.due_date - datetime.utcnow()).total_seconds() / 3600
        
        tasks_info.append({
            "id": task.id,
            "title": task.title,
            "pillar": task.pillar.value,
            "current_priority": task.priority.value,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "time_until_deadline_hours": time_until_deadline,
            "estimated_duration_minutes": task.estimated_duration,
            "status": task.status.value,
            "has_dependency": task.depends_on_task_id is not None
        })
    
    prompt = f"""Analyze and prioritize these tasks for a productivity-focused user.

Tasks:
{chr(10).join([f"- {t['title']} (Pillar: {t['pillar']}, Current Priority: {t['current_priority']}, Due: {t['due_date'] or 'No deadline'}, Est. Duration: {t['estimated_duration_minutes'] or 'Unknown'} min)" for t in tasks_info])}

Context:
- Current time: {datetime.utcnow().isoformat()}
- User patterns: {[h.pattern_type for h in habits[:3]]}

Consider:
1. Deadline urgency (time until deadline vs estimated duration)
2. Task dependencies (blocked tasks should be lower priority)
3. Workload balance (don't overload with too many urgent tasks)
4. Strategic importance (work/education may be more critical)
5. Time of day patterns (user may be more productive at certain times)

For each task, provide:
- Priority score (0-100, higher = more urgent)
- Recommended priority level (low/medium/high/urgent)
- Brief reasoning

Respond in JSON format:
{{
  "priorities": [
    {{
      "task_id": <id>,
      "priority_score": <0-100>,
      "recommended_priority": "<low|medium|high|urgent>",
      "reasoning": "<brief explanation>"
    }}
  ]
}}
"""
    
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        
        import json
        # Try to extract JSON from response
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from markdown code blocks if present
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]
        
        result = json.loads(content)
        
        # Map to tasks
        prioritized = []
        for item in result.get("priorities", []):
            task_id = item.get("task_id")
            task = next((t for t in tasks if t.id == task_id), None)
            if task:
                prioritized.append({
                    "task": task,
                    "priority_score": item.get("priority_score", 50),
                    "recommended_priority": item.get("recommended_priority", "medium"),
                    "reasoning": item.get("reasoning", "")
                })
        
        # Sort by priority score (descending)
        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return prioritized
    except Exception as e:
        logger.error(f"Error in AI prioritization: {e}")
        # Fallback to simple priority ordering
        return [
            {
                "task": task,
                "priority_score": 50,
                "recommended_priority": task.priority.value,
                "reasoning": "Fallback prioritization"
            }
            for task in sorted(tasks, key=lambda t: (t.priority.value, t.due_date or datetime.max))
        ]


async def apply_ai_prioritization(
    session: AsyncSession,
    user_id: int,
    auto_apply: bool = False
) -> List[Dict[str, Any]]:
    """
    Apply AI prioritization to user's tasks.
    
    Args:
        session: Database session
        user_id: User ID
        auto_apply: If True, automatically update priorities. If False, return suggestions.
    
    Returns:
        List of prioritization suggestions
    """
    # Get active tasks
    stmt = select(Task).where(
        and_(
            Task.user_id == user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        )
    )
    result = await session.execute(stmt)
    tasks = list(result.scalars().all())
    
    if not tasks:
        return []
    
    # Get AI prioritization
    prioritized = await ai_prioritize_tasks(session, user_id, tasks)
    
    # Apply if auto_apply is True
    if auto_apply:
        for item in prioritized:
            task = item["task"]
            recommended = item["recommended_priority"]
            try:
                priority_enum = TaskPriority(recommended)
                if task.priority != priority_enum:
                    old_priority = task.priority
                    task.priority = priority_enum
                    logger.info(
                        f"Updated task {task.id} priority from {old_priority.value} to {recommended}"
                    )
            except ValueError:
                pass
        
        await session.flush()
    
    return prioritized

