from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.models.user_skill import UserSkill

from app.models.session import Session
from app.models.feedback import Feedback
from app.models.badge import Badge
from app.models.session_request import SessionRequest

def get_top_teach_skills(
    db: Session
):

    return (
        db.query(
            Skill.id,
            Skill.name,
            func.count(
                UserSkill.id
            ).label(
                "count"
            )
        )
        .join(
            UserSkill,
            Skill.id == UserSkill.skill_id
        )
        .filter(
            UserSkill.type == "teach"
        )
        .group_by(
            Skill.id,
            Skill.name
        )
        .order_by(
            func.count(
                UserSkill.id
            ).desc()
        )
        .all()
    )


def get_top_learn_skills(
    db: Session
):

    return (
        db.query(
            Skill.id,
            Skill.name,
            func.count(
                UserSkill.id
            ).label(
                "count"
            )
        )
        .join(
            UserSkill,
            Skill.id == UserSkill.skill_id
        )
        .filter(
            UserSkill.type == "learn"
        )
        .group_by(
            Skill.id,
            Skill.name
        )
        .order_by(
            func.count(
                UserSkill.id
            ).desc()
        )
        .all()
    )

def get_mentor_metrics(
    db: Session,
    user_id: int
):

    completed_sessions = (
        db.query(Session)
        .filter(
            Session.mentor_id == user_id,
            Session.status == "completed"
        )
        .count()
    )

    cancelled_sessions = (
        db.query(Session)
        .filter(
            Session.mentor_id == user_id,
            Session.status == "cancelled"
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

    accepted_requests = (
        db.query(SessionRequest)
        .filter(
            SessionRequest.receiver_id == user_id,
            SessionRequest.status == "accepted"
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

    badges_count = (
        db.query(Badge)
        .filter(
            Badge.user_id == user_id
        )
        .count()
    )

    return {
        "completed_sessions": completed_sessions,
        "cancelled_sessions": cancelled_sessions,
        "average_rating": average_rating or 0,
        "accepted_requests": accepted_requests,
        "received_requests": received_requests,
        "badges_count": badges_count
    }