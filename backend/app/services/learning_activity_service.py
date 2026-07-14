from sqlalchemy.orm import Session
from app.repositories.learning_activity_repository import (
    create_learning_activity,
    get_user_activities
)
from typing import Optional, Dict, Any, List


def record_learning_activity(
    db: Session,
    user_id: int,
    activity_type: str,
    entity_type: str,
    entity_id: int,
    activity_data: Optional[dict] = None
):
    return create_learning_activity(
        db,
        user_id,
        activity_type,
        entity_type,
        entity_id,
        activity_data
    )


def get_user_activity_history(
    db: Session,
    user_id: int,
    page: int = 1,
    size: int = 20,
    activity_type: Optional[str] = None
):
    return get_user_activities(
        db,
        user_id,
        page,
        size,
        activity_type
    )
