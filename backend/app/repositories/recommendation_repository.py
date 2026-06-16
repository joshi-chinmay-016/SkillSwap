from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.feedback import Feedback
from app.models.session import Session as SessionModel
from app.models.user_skill import UserSkill
from app.models.user import User

def get_mentors_for_skill(
    db: Session,
    skill_id: int
):

    return (
        db.query(UserSkill.user_id)
        .filter(
            UserSkill.skill_id == skill_id,
            UserSkill.type == "teach"
        )
        .all()
    )


def get_average_rating(
    db: Session,
    user_id: int
):

    result = (
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

    return result or 0


def get_completed_sessions(
    db: Session,
    user_id: int
):

    return (
        db.query(SessionModel)
        .filter(
            SessionModel.mentor_id == user_id,
            SessionModel.status == "completed"
        )
        .count()
    )

def get_user_name(
    db: Session,
    user_id: int
):

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    return user.name

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