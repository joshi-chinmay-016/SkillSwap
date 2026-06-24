from sqlalchemy.orm import Session

from app.services.wallet_service import (
    credit_wallet
)


def reward_session_completion(
    db: Session,
    user_id: int
):

    return credit_wallet(
        db,
        user_id,
        10,
        "Session Completed"
    )


def reward_feedback_received(
    db: Session,
    user_id: int
):

    return credit_wallet(
        db,
        user_id,
        5,
        "Feedback Received"
    )


def reward_badge_earned(
    db: Session,
    user_id: int,
    badge_name: str
):

    return credit_wallet(
        db,
        user_id,
        15,
        f"Badge Earned: {badge_name}"
    )