from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.session import Session as SessionModel
from app.models.feedback import Feedback
from app.models.badge import Badge
from app.models.session_request import SessionRequest
from app.models.user_skill import UserSkill
from app.repositories.feedback_repository import get_rating_count
def get_dashboard_stats(
    db: Session,
    user_id: int
):

    completed_sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.mentor_id == user_id,
            SessionModel.status == "completed"
        )
        .count()
    )

    scheduled_sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.mentor_id == user_id,
            SessionModel.status == "scheduled"
        )
        .count()
    )

    cancelled_sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.mentor_id == user_id,
            SessionModel.status == "cancelled"
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

    badges_count = (
        db.query(Badge)
        .filter(
            Badge.user_id == user_id
        )
        .count()
    )

    requests_sent = (
        db.query(SessionRequest)
        .filter(
            SessionRequest.sender_id == user_id
        )
        .count()
    )

    requests_received = (
        db.query(SessionRequest)
        .filter(
            SessionRequest.receiver_id == user_id
        )
        .count()
    )

    skills_teaching = (
        db.query(UserSkill)
        .filter(
            UserSkill.user_id == user_id,
            UserSkill.type == "teach"
        )
        .count()
    )

    skills_learning = (
        db.query(UserSkill)
        .filter(
            UserSkill.user_id == user_id,
            UserSkill.type == "learn"
        )
        .count()
    )
    five_star_reviews = get_rating_count(
    db,
    user_id,
    5
)

    four_star_reviews = get_rating_count(
    db,
    user_id,
    4
)

    three_star_reviews = get_rating_count(
    db,
    user_id,
    3
)
    
    return {
        "completed_sessions": completed_sessions,
        "scheduled_sessions": scheduled_sessions,
        "cancelled_sessions": cancelled_sessions,

        "average_rating": round(
            float(average_rating),
            2
        ) if average_rating else 0,

        "feedback_count": feedback_count,
        "badges_count": badges_count,

        "requests_sent": requests_sent,
        "requests_received": requests_received,

        "skills_teaching": skills_teaching,
        "skills_learning": skills_learning,
        "five_star_reviews": five_star_reviews,

        "four_star_reviews": four_star_reviews,

        "three_star_reviews": three_star_reviews
    }