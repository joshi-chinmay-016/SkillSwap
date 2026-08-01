"""
SessionSummaryTool — retrieves the latest session summary for the user.

Reuses:
    - journey_service.get_my_journeys()
    - session_summary_service (internal repo access via get_summary)

Does NOT regenerate summaries — reuses Day 60 persisted data.
"""
import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.ai.models.mentor_intent import MentorIntent
from app.ai.tools.mentor_tool import MentorTool

logger = logging.getLogger(__name__)


class SessionSummaryTool(MentorTool):
    """Retrieves the latest session summary from persisted data."""

    @property
    def name(self) -> str:
        return "SessionSummaryTool"

    @property
    def description(self) -> str:
        return "Retrieves the latest session summary, takeaways, and follow-ups."

    @property
    def supported_intents(self) -> List[MentorIntent]:
        return [MentorIntent.SESSION_SUMMARY]

    def _execute(
        self,
        db: Session,
        user_id: int,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        from app.repositories.session_summary_repository import (
            get_session_summary as repo_get_session_summary,
        )
        from app.models.learning_session import LearningSession
        from sqlalchemy import desc

        # Find the user's most recent completed session
        latest_session = (
            db.query(LearningSession)
            .filter(
                LearningSession.user_id == user_id,
                LearningSession.status == "COMPLETED",
            )
            .order_by(desc(LearningSession.ended_at))
            .first()
        )

        if not latest_session:
            return {
                "has_summary": False,
                "message": "No completed sessions found.",
            }

        # Retrieve the summary for the latest session
        summary = repo_get_session_summary(db, latest_session.id)
        if not summary:
            return {
                "has_summary": False,
                "session_title": latest_session.title,
                "message": "No summary available for the latest session.",
            }

        return {
            "has_summary": True,
            "session_id": latest_session.id,
            "session_title": latest_session.title,
            "summary": summary.summary,
            "key_takeaways": summary.key_takeaways or [],
            "strengths": summary.strengths or [],
            "weaknesses": summary.weaknesses or [],
            "follow_up_topics": summary.follow_up_topics or [],
            "created_at": str(summary.created_at) if summary.created_at else None,
        }
