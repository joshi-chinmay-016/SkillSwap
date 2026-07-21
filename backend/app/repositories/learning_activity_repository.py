from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.learning_activity import LearningActivity
from typing import List, Optional
from datetime import datetime, date


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


def get_user_heatmap_data(
    db: Session,
    user_id: int
) -> List[dict]:
    date_col = func.date(LearningActivity.created_at)
    results = (
        db.query(
            date_col.label("date"),
            func.count().label("count")
        )
        .filter(LearningActivity.user_id == user_id)
        .group_by(date_col)
        .order_by(date_col.asc())
        .all()
    )

    return [
        {
            "date": str(row.date),
            "count": int(row.count)
        }
        for row in results
    ]


def get_user_distinct_activity_dates(
    db: Session,
    user_id: int
) -> List[date]:
    """
    Retrieves distinct activity dates for the given user ordered chronologically ascending.
    """
    date_col = func.date(LearningActivity.created_at)
    results = (
        db.query(date_col.label("date"))
        .filter(LearningActivity.user_id == user_id)
        .group_by(date_col)
        .order_by(date_col.asc())
        .all()
    )

    distinct_dates = []
    for row in results:
        d = row.date
        if isinstance(d, str):
            d = datetime.strptime(d, "%Y-%m-%d").date()
        elif isinstance(d, datetime):
            d = d.date()
        if d and d not in distinct_dates:
            distinct_dates.append(d)

    return distinct_dates


