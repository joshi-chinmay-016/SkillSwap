from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.badge import Badge
from app.models.session import Session as SessionModel
from app.models.feedback import Feedback
from app.models.session_request import SessionRequest

from app.repositories.badge_repository import (
    create_badge,
    get_user_badges
)

from app.services.notification_service import (
    create_user_notification
)


def award_badges(
    db: Session,
    user_id: int
):

    existing = get_user_badges(
        db,
        user_id
    )

    names = {
        badge.name
        for badge in existing
    }

    completed_sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.mentor_id == user_id,
            SessionModel.status == "completed"
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

    received_requests = (
        db.query(SessionRequest)
        .filter(
            SessionRequest.receiver_id == user_id
        )
        .count()
    )

    accepted_requests = (
        db.query(SessionRequest)
        .filter(
            SessionRequest.receiver_id == user_id,
            SessionRequest.status == "accepted"
        )
        .count()
    )

    response_rate = (
        accepted_requests
        /
        received_requests
        *
        100
        if received_requests > 0
        else 0
    )

    # First Session

    if (
        completed_sessions >= 1
        and "First Session" not in names
    ):

        create_badge(
            db,
            Badge(
                user_id=user_id,
                name="First Session",
                description="Completed first mentoring session"
            )
        )

        create_user_notification(
            db,
            user_id,
            "🏅 Badge Earned: First Session"
        )

    # Active Mentor

    if (
        completed_sessions >= 5
        and "Active Mentor" not in names
    ):

        create_badge(
            db,
            Badge(
                user_id=user_id,
                name="Active Mentor",
                description="Completed 5 mentoring sessions"
            )
        )

        create_user_notification(
            db,
            user_id,
            "🏅 Badge Earned: Active Mentor"
        )

    # Top Rated Mentor

    if (
        average_rating
        and average_rating >= 4.5
        and feedback_count >= 3
        and "Top Rated Mentor" not in names
    ):

        create_badge(
            db,
            Badge(
                user_id=user_id,
                name="Top Rated Mentor",
                description="Maintained rating above 4.5"
            )
        )

        create_user_notification(
            db,
            user_id,
            "🏅 Badge Earned: Top Rated Mentor"
        )

    # Fast Responder

    if (
        response_rate >= 80
        and received_requests >= 3
        and "Fast Responder" not in names
    ):

        create_badge(
            db,
            Badge(
                user_id=user_id,
                name="Fast Responder",
                description="Accepted over 80% of incoming requests"
            )
        )

        create_user_notification(
            db,
            user_id,
            "🏅 Badge Earned: Fast Responder"
        )

    return get_user_badges(
        db,
        user_id
    )


def my_badges(
    db: Session,
    user_id: int
):

    return get_user_badges(
        db,
        user_id
    )