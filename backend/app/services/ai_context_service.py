import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models.ai_context import AIContext

logger = logging.getLogger(__name__)


def get_user_ai_context(db: Session, user_id: int) -> Optional[AIContext]:
    """
    Retrieve the persistent AI Context for a given user_id.
    Returns None if no context exists yet.
    """
    try:
        return (
            db.query(AIContext)
            .filter(AIContext.user_id == user_id)
            .first()
        )
    except Exception as exc:
        logger.error("Failed to fetch AIContext for user_id=%d: %s", user_id, str(exc))
        return None
