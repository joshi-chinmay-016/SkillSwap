from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.feedback import (
    Feedback
)


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