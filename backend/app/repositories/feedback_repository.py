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

def get_feedback_count(
    db: Session,
    user_id: int
):

    return (
        db.query(Feedback)
        .filter(
            Feedback.reviewee_id == user_id
        )
        .count()
    )


def get_rating_count(
    db: Session,
    user_id: int,
    rating: int
):

    return (
        db.query(Feedback)
        .filter(
            Feedback.reviewee_id == user_id,
            Feedback.rating == rating
        )
        .count()
    )


def get_latest_reviews(
    db: Session,
    user_id: int,
    limit: int = 5
):

    return (
        db.query(Feedback)
        .filter(
            Feedback.reviewee_id == user_id
        )
        .order_by(
            Feedback.id.desc()
        )
        .limit(limit)
        .all()
    )