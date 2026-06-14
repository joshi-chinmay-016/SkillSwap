from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.feedback import Feedback


def create_feedback(
    db: Session,
    feedback: Feedback
):

    db.add(feedback)

    db.commit()

    db.refresh(feedback)

    return feedback


def get_feedback_by_user(
    db: Session,
    user_id: int
):

    return (
        db.query(Feedback)
        .filter(
            Feedback.reviewee_id == user_id
        )
        .all()
    )


def get_average_rating(
    db: Session,
    user_id: int
):

    return (
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