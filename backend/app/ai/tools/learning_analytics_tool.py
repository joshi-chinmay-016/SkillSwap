"""
LearningAnalyticsTool — retrieves learning analytics data for the user.

Reuses:
    - learning_activity_service.get_user_learning_analytics()
    - learning_activity_service.get_user_learning_streak()
"""
import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.ai.models.mentor_intent import MentorIntent
from app.ai.tools.mentor_tool import MentorTool

logger = logging.getLogger(__name__)


class LearningAnalyticsTool(MentorTool):
    """Retrieves aggregated learning analytics from platform data."""

    @property
    def name(self) -> str:
        return "LearningAnalyticsTool"

    @property
    def description(self) -> str:
        return "Retrieves learning analytics: trends, velocity, activity breakdown."

    @property
    def supported_intents(self) -> List[MentorIntent]:
        return [MentorIntent.LEARNING_ANALYTICS]

    def _execute(
        self,
        db: Session,
        user_id: int,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        from app.services.learning_activity_service import (
            get_user_learning_analytics,
            get_user_learning_streak,
        )

        analytics = get_user_learning_analytics(db, user_id)
        streak = get_user_learning_streak(db, user_id)

        # Build a concise summary suitable for LLM prompt injection
        weekly_summary = {}
        if analytics.weekly_activity:
            # Only include non-zero days for conciseness
            weekly_summary = {
                day: count
                for day, count in analytics.weekly_activity.items()
                if count > 0
            }

        trend_info = None
        if analytics.learning_trend:
            trend_info = {
                "direction": analytics.learning_trend.direction,
                "percentage": analytics.learning_trend.percentage,
            }

        most_active = None
        if analytics.most_active_day:
            most_active = {
                "day": analytics.most_active_day.day,
                "count": analytics.most_active_day.count,
            }

        summary_info = None
        if analytics.summary:
            summary_info = {
                "total_activities": analytics.summary.total_activities,
                "total_active_days": analytics.summary.total_active_days,
                "average_per_day": analytics.summary.average_per_day,
            }

        return {
            "weekly_activity": weekly_summary,
            "learning_trend": trend_info,
            "learning_velocity": analytics.learning_velocity,
            "most_active_day": most_active,
            "average_per_day": analytics.average_per_day,
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
            "consistency_score": streak.consistency_score if streak else 0.0,
            "summary": summary_info,
        }
