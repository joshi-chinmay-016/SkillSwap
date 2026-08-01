"""
AIContextTool — retrieves the learner's AI profile data.

Reuses:
    - ai_context_service.get_user_ai_context()

Never duplicates context logic.
"""
import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.ai.models.mentor_intent import MentorIntent
from app.ai.tools.mentor_tool import MentorTool

logger = logging.getLogger(__name__)


class AIContextTool(MentorTool):
    """Retrieves the learner's persistent AI Context profile."""

    @property
    def name(self) -> str:
        return "AIContextTool"

    @property
    def description(self) -> str:
        return "Retrieves learning profile: strengths, weaknesses, interests, style."

    @property
    def supported_intents(self) -> List[MentorIntent]:
        return [MentorIntent.PROFILE_INFORMATION]

    def _execute(
        self,
        db: Session,
        user_id: int,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        from app.services.ai_context_service import get_user_ai_context

        context = get_user_ai_context(db, user_id)

        if not context:
            return {
                "has_profile": False,
                "message": "No learning profile found. Complete some sessions first.",
            }

        return {
            "has_profile": True,
            "strong_topics": context.strong_topics or [],
            "weak_topics": context.weak_topics or [],
            "learning_interests": context.learning_interests or [],
            "learning_style": context.learning_style or "",
            "recommended_topics": context.recommended_topics or [],
            "completed_sessions": context.completed_sessions or 0,
            "overall_summary": context.overall_summary or "",
        }
