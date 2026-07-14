from sqlalchemy.orm import Session
from app.models.learning_activity import LearningActivity
from typing import List, Optional
from datetime import datetime


def create_learning_activity(
    db: Session,
    user_id: int,
    activity_type: str,
    entity_type: str,
    entity_id: int,
    activity_data: Optional[dict] = None
) -> LearningActivity:
    activity = LearningActivity(
        user_id=user_id,
        activity_type=activity_type,
        entity_type=entity_type,
        entity_id=entity_id,
        activity_data=activity_data
    )
    db.add(activity)
    return activity


def get_user_activities(
    db: Session,
    user_id: int,
    page: int = 1,
    size: int = 20,
    activity_type: Optional[str] = None
) -> tuple[List[LearningActivity], int]:
    query = db.query(LearningActivity).filter(
        LearningActivity.user_id == user_id
    )

    if activity_type:
        query = query.filter(LearningActivity.activity_type == activity_type)

    total = query.count()

    activities = (
        query
        .order_by(LearningActivity.created_at.desc(), LearningActivity.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return activities, total
