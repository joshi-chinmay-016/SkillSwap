"""
JourneyTool — retrieves learning journey data for the user.

Reuses:
    - journey_service.get_my_journeys()
    - journey_service.get_active_journey()
"""
import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.ai.models.mentor_intent import MentorIntent
from app.ai.tools.mentor_tool import MentorTool

logger = logging.getLogger(__name__)


class JourneyTool(MentorTool):
    """Retrieves the learner's journey data including milestones."""

    @property
    def name(self) -> str:
        return "JourneyTool"

    @property
    def description(self) -> str:
        return "Retrieves active/completed journeys, milestones, and progress."

    @property
    def supported_intents(self) -> List[MentorIntent]:
        return [MentorIntent.LEARNING_JOURNEY]

    def _execute(
        self,
        db: Session,
        user_id: int,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        from app.services.journey_service import get_my_journeys, get_active_journey

        all_journeys = get_my_journeys(db, user_id)
        active_journey = get_active_journey(db, user_id)

        # Summarise all journeys
        journey_summaries = []
        for j in (all_journeys or []):
            journey_summaries.append({
                "id": j.id,
                "title": j.title,
                "target_role": j.target_role,
                "status": j.status,
                "progress_percentage": round(j.progress_percentage or 0.0, 1),
                "current_week": j.current_week,
                "total_weeks": j.total_weeks,
            })

        completed_count = len([j for j in (all_journeys or []) if j.status == "completed"])

        # Active journey detail with next milestone
        current_detail = None
        next_milestone = None
        if active_journey:
            current_detail = {
                "id": active_journey.id,
                "title": active_journey.title,
                "target_role": active_journey.target_role,
                "progress_percentage": round(active_journey.progress_percentage or 0.0, 1),
                "current_week": active_journey.current_week,
                "total_weeks": active_journey.total_weeks,
            }
            # Find next pending/in_progress milestone
            if active_journey.milestones:
                for m in active_journey.milestones:
                    if m.status in ("pending", "in_progress"):
                        next_milestone = {
                            "week_number": m.week_number,
                            "topic": m.topic,
                            "goal": m.goal,
                            "status": m.status,
                        }
                        break

        return {
            "total_journeys": len(all_journeys or []),
            "completed_journeys": completed_count,
            "journeys": journey_summaries,
            "current_journey": current_detail,
            "next_milestone": next_milestone,
        }
