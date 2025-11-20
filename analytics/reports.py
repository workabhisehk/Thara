"""
Report generation.
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from analytics.completion_tracking import get_weekly_stats, get_pillar_stats
from analytics.readiness_forecasting import calculate_readiness_scores
from database.connection import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def generate_weekly_report(user_id: int) -> str:
    """
    Generate weekly report text.
    
    Args:
        user_id: User ID
    
    Returns:
        Formatted report text
    """
    async with AsyncSessionLocal() as session:
        # Get stats
        weekly_stats = await get_weekly_stats(session, user_id)
        pillar_stats = await get_pillar_stats(session, user_id, days=7)
        readiness = await calculate_readiness_scores(session, user_id)
        
        # Format report
        report = "📊 **Weekly Report**\n\n"
        
        report += "**Summary:**\n"
        report += f"• Tasks completed: {weekly_stats.get('completed', 0)}\n"
        report += f"• Tasks created: {weekly_stats.get('created', 0)}\n"
        report += f"• Completion rate: {weekly_stats.get('completion_rate', 0):.1f}%\n"
        report += f"• Overdue tasks: {weekly_stats.get('overdue', 0)}\n\n"
        
        report += "**By Category:**\n"
        for pillar, stats in pillar_stats.items():
            if stats.get('total', 0) > 0:
                report += f"• {pillar.capitalize()}: {stats.get('completed', 0)}/{stats.get('total', 0)} ({stats.get('completion_rate', 0):.1f}%)\n"
        
        if readiness:
            report += "\n**Upcoming Deadlines:**\n"
            for item in readiness[:5]:
                score = item.get('readiness_score', 0)
                emoji = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
                report += f"{emoji} {item.get('task_title')}: {score:.0f}% ready\n"
        
        return report

