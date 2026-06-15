from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.session import Session as SessionModel
from app.models.feedback import Feedback
from app.models.badge import Badge


def get_dashboard_stats(
    db: Session,
    user_id: int
):

    completed_sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.mentor_id == user_id,
            SessionModel.status == "completed"
        )
        .count()
    )

    scheduled_sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.mentor_id == user_id,
            SessionModel.status == "scheduled"
        )
        .count()
    )

    average_rating = (
        db.query(
            func.avg(
                Feedback.rating
            )
        )
        .filter(
            Feedback.reviewee_id == user_id
        )
        .scalar()
    )

    feedback_count = (
        db.query(Feedback)
        .filter(
            Feedback.reviewee_id == user_id
        )
        .count()
    )

    badges_count = (
        db.query(Badge)
        .filter(
            Badge.user_id == user_id
        )
        .count()
    )

    return {
        "completed_sessions": completed_sessions,
        "scheduled_sessions": scheduled_sessions,
        "average_rating": round(
            float(average_rating),
            2
        ) if average_rating else 0,
        "feedback_count": feedback_count,
        "badges_count": badges_count
    }