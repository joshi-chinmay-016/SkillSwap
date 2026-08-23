from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from app.models.feedback import Feedback
from app.models.session import Session as SessionModel
from app.models.user import User
from app.repositories.feedback_repository import (
    create_feedback,
    get_feedback_by_user,
    get_average_rating,
    get_feedback_count,
    get_rating_count,
    get_latest_reviews
)
from app.services.reward_service import reward_feedback_received
from app.services.notification_service import create_user_notification
from app.core.logging import log_structured_event

logger = logging.getLogger("skillswap.feedback")


def submit_feedback(
    db: Session,
    session_id: int,
    reviewer_id: int,
    reviewee_id: int | None,
    rating: int,
    comment: str
) -> Feedback:
    # 1. Session existence check
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referenced session does not exist."
        )

    # Auto-infer counterpart reviewee if omitted
    if not reviewee_id:
        if reviewer_id == session.mentor_id:
            reviewee_id = session.requester_id
        elif reviewer_id == session.requester_id:
            reviewee_id = session.mentor_id
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to submit feedback for a session you did not participate in."
            )

    # 2. Rating validation
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be an integer between 1 and 5."
        )

    clean_comment = (comment or "").strip()
    if not clean_comment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback comment cannot be empty."
        )
    if len(clean_comment) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback comment cannot exceed 500 characters."
        )

    # 3. Prevent self-feedback
    if reviewer_id == reviewee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot submit feedback for yourself."
        )

    if session.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit feedback for a session that is {session.status}. The session must be completed first."
        )

    # 4. Participant authorization check
    participants = {session.mentor_id, session.requester_id}
    if reviewer_id not in participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to submit feedback for a session you did not participate in."
        )
    if reviewee_id not in participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The reviewee is not a participant of this session."
        )

    # 5. Duplicate feedback check (one feedback per participant per session)
    existing_feedback = (
        db.query(Feedback)
        .filter(
            Feedback.session_id == session_id,
            Feedback.reviewer_id == reviewer_id
        )
        .first()
    )
    if existing_feedback:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted feedback for this session."
        )

    # 6. Create & Persist feedback
    feedback = Feedback(
        session_id=session_id,
        reviewer_id=reviewer_id,
        reviewee_id=reviewee_id,
        rating=rating,
        comment=clean_comment
    )

    saved_feedback = create_feedback(db, feedback)

    # 7. Reward reviewee
    try:
        reward_feedback_received(db, reviewee_id)
    except Exception as e:
        logger.warning(f"Failed to reward feedback: {e}")

    # 8. Notify reviewee
    try:
        reviewer = db.query(User).filter(User.id == reviewer_id).first()
        reviewer_name = reviewer.name if reviewer else "A peer learner"
        create_user_notification(
            db=db,
            user_id=reviewee_id,
            title="New Review Received ⭐",
            message=f"{reviewer_name} gave you a {rating}-star rating: \"{clean_comment[:60]}...\"",
            type="FEEDBACK_RECEIVED",
            related_session_id=session_id
        )
    except Exception:
        pass

    log_structured_event(
        "feedback_submitted",
        session_id=session_id,
        reviewer_id=reviewer_id,
        reviewee_id=reviewee_id,
        rating=rating
    )

    return saved_feedback


def get_feedback_for_session(
    db: Session,
    session_id: int,
    current_user_id: int
) -> list[Feedback]:
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    if current_user_id not in (session.mentor_id, session.requester_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view feedback for this private session."
        )

    return (
        db.query(Feedback)
        .filter(Feedback.session_id == session_id)
        .all()
    )


def user_feedback(
    db: Session,
    user_id: int
):
    return get_feedback_by_user(db, user_id)


def my_rating(
    db: Session,
    user_id: int
):
    avg = get_average_rating(db, user_id)
    return round(avg, 2) if avg else 0.0


def feedback_stats(
    db: Session,
    user_id: int
):
    avg = get_average_rating(db, user_id)
    return {
        "average_rating": round(avg, 2) if avg else 0.0,
        "total_reviews": get_feedback_count(db, user_id),
        "five_star_reviews": get_rating_count(db, user_id, 5),
        "four_star_reviews": get_rating_count(db, user_id, 4),
        "three_star_reviews": get_rating_count(db, user_id, 3),
        "two_star_reviews": get_rating_count(db, user_id, 2),
        "one_star_reviews": get_rating_count(db, user_id, 1)
    }


def review_summary(
    db: Session,
    user_id: int
):
    reviews = get_latest_reviews(db, user_id)
    return {
        "latest_reviews": [
            {
                "rating": review.rating,
                "comment": review.comment
            }
            for review in reviews
        ]
    }