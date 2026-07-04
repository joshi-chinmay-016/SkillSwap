from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.feedback import (
    Feedback
)

from app.models.session import Session
from app.models.user import User

def get_top_rated_users(
    db: Session
):

    return (
        db.query(
            Feedback.reviewee_id.label(
                "user_id"
            ),
            func.avg(
                Feedback.rating
            ).label(
                "average_rating"
            ),
            func.count(
                Feedback.id
            ).label(
                "total_reviews"
            )
        )
        .group_by(
            Feedback.reviewee_id
        )
        .order_by(
            func.avg(
                Feedback.rating
            ).desc()
        )
        .limit(10)
        .all()
    )

def get_most_active_mentors(
    db: Session
):

    return (
        db.query(
            Session.mentor_id.label(
                "user_id"
            ),
            func.count(
                Session.id
            ).label(
                "completed_sessions"
            )
        )
        .filter(
            Session.status
            ==
            "completed"
        )
        .group_by(
            Session.mentor_id
        )
        .order_by(
            func.count(
                Session.id
            ).desc()
        )
        .limit(10)
        .all()
    )

def get_all_mentors(
    db: Session
):

    return (
        db.query(
            User.id
        )
        .all()
    )