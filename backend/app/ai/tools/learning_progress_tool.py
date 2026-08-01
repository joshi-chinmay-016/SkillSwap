"""
LearningProgressTool — retrieves real learning progress data for the user.

Reuses:
    - journey_service.get_my_journeys()
    - learning_activity_service.get_user_learning_streak()
    - ai_context_service.get_user_ai_context()
"""
import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.ai.models.mentor_intent import MentorIntent
from app.ai.tools.mentor_tool import MentorTool

logger = logging.getLogger(__name__)


class LearningProgressTool(MentorTool):
    """Retrieves the learner's overall progress from platform data."""

    @property
    def name(self) -> str:
        return "LearningProgressTool"

    @property
    def description(self) -> str:
        return "Retrieves learning progress: journeys, sessions, streaks, completion."

    @property
    def supported_intents(self) -> List[MentorIntent]:
        return [MentorIntent.LEARNING_PROGRESS]

    def _execute(
        self,
        db: Session,
        user_id: int,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        from app.services.journey_service import get_my_journeys
        from app.services.learning_activity_service import get_user_learning_streak
        from app.services.ai_context_service import get_user_ai_context

        # Journey data
        journeys = get_my_journeys(db, user_id)
        total_journeys = len(journeys) if journeys else 0
        completed_journeys = (
            len([j for j in journeys if j.status == "completed"])
            if journeys else 0
        )

        # Completion percentage across all journeys
        if total_journeys > 0:
            total_progress = sum(j.progress_percentage or 0.0 for j in journeys)
            avg_completion = round(total_progress / total_journeys, 1)
        else:
            avg_completion = 0.0

        # AI Context for completed_sessions count
        context = get_user_ai_context(db, user_id)
        completed_sessions = context.completed_sessions if context else 0

        # Streak data
        streak = get_user_learning_streak(db, user_id)
        last_activity = streak.last_active_date if streak else None

        return {
            "total_journeys": total_journeys,
            "completed_journeys": completed_journeys,
            "completed_sessions": completed_sessions,
            "completion_percentage": avg_completion,
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
            "last_activity": last_activity,
        }
