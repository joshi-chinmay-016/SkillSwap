from sqlalchemy.orm import Session

from app.models.feedback import (
    Feedback
)

from app.repositories.feedback_repository import (
    create_feedback,
    get_feedback_by_user,
    get_average_rating
)


def submit_feedback(
    db: Session,
    session_id: int,
    reviewer_id: int,
    reviewee_id: int,
    rating: int,
    comment: str
):

    feedback = Feedback(
        session_id=session_id,
        reviewer_id=reviewer_id,
        reviewee_id=reviewee_id,
        rating=rating,
        comment=comment
    )

    return create_feedback(
        db,
        feedback
    )


def user_feedback(
    db: Session,
    user_id: int
):

    return get_feedback_by_user(
        db,
        user_id
    )


def my_rating(
    db: Session,
    user_id: int
):

    avg = get_average_rating(
        db,
        user_id
    )

    return round(avg, 2) if avg else 0