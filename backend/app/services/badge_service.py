from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.badge import Badge
from app.models.session import Session as SessionModel
from app.models.feedback import Feedback

from app.repositories.badge_repository import (
    create_badge,
    get_user_badges
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
        db.query(
            SessionModel
        )
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

    if (
        completed_sessions >= 5
        and "5 Sessions Completed" not in names
    ):

        create_badge(
            db,
            Badge(
                user_id=user_id,
                name="5 Sessions Completed",
                description="Completed five mentoring sessions"
            )
        )

    if (
        average_rating
        and average_rating >= 4.5
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