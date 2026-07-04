from sqlalchemy.orm import Session

from app.models.feedback import (
    Feedback
)

from app.repositories.feedback_repository import (
    create_feedback,
    get_feedback_by_user,
    get_average_rating,
    get_feedback_count,
    get_rating_count,
    get_latest_reviews
)
from app.services.reward_service import (
    reward_feedback_received
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

    saved_feedback = create_feedback(
        db,
        feedback
    )

    reward_feedback_received(
        db,
        reviewee_id
    )

    return saved_feedback
   


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

def feedback_stats(
    db: Session,
    user_id: int
):

    avg = get_average_rating(
        db,
        user_id
    )

    return {
        "average_rating":
        round(avg, 2)
        if avg else 0,

        "total_reviews":
        get_feedback_count(
            db,
            user_id
        ),

        "five_star_reviews":
        get_rating_count(
            db,
            user_id,
            5
        ),

        "four_star_reviews":
        get_rating_count(
            db,
            user_id,
            4
        ),

        "three_star_reviews":
        get_rating_count(
            db,
            user_id,
            3
        ),

        "two_star_reviews":
        get_rating_count(
            db,
            user_id,
            2
        ),

        "one_star_reviews":
        get_rating_count(
            db,
            user_id,
            1
        )
    }


def review_summary(
    db: Session,
    user_id: int
):

    reviews = get_latest_reviews(
        db,
        user_id
    )

    return {
        "latest_reviews": [
            {
                "rating": review.rating,
                "comment": review.comment
            }
            for review in reviews
        ]
    }