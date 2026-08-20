from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from app.models.feedback import Feedback
from app.models.session import Session as SessionModel
from app.models.user_skill import UserSkill
from app.models.user import User
from app.models.profile import Profile
from app.models.mentor_availability import MentorAvailability
from app.models.journey import LearningJourney


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


def get_user_skills_by_type(
    db: Session,
    user_id: int,
    skill_type: str
):
    return (
        db.query(UserSkill)
        .options(joinedload(UserSkill.skill))
        .filter(
            UserSkill.user_id == user_id,
            UserSkill.type == skill_type
        )
        .all()
    )


def get_candidate_mentors_for_skills(
    db: Session,
    current_user_id: int,
    skill_ids: list[int]
):
    if not skill_ids:
        return []

    return (
        db.query(UserSkill)
        .options(joinedload(UserSkill.skill), joinedload(UserSkill.user))
        .filter(
            UserSkill.skill_id.in_(skill_ids),
            UserSkill.type == "teach",
            UserSkill.user_id != current_user_id
        )
        .all()
    )


def get_profile_by_user_id(
    db: Session,
    user_id: int
):
    return (
        db.query(Profile)
        .filter(Profile.user_id == user_id)
        .first()
    )


def get_user_active_journeys(
    db: Session,
    user_id: int
):
    return (
        db.query(LearningJourney)
        .filter(
            LearningJourney.user_id == user_id,
            or_(
                LearningJourney.status == "ACTIVE",
                LearningJourney.status == "active"
            )
        )
        .all()
    )


def get_average_rating(
    db: Session,
    user_id: int
):
    result = (
        db.query(
            func.avg(Feedback.rating)
        )
        .filter(
            Feedback.reviewee_id == user_id
        )
        .scalar()
    )
    return float(result or 0.0)


def get_completed_sessions(
    db: Session,
    user_id: int
):
    return (
        db.query(SessionModel)
        .filter(
            SessionModel.mentor_id == user_id,
            or_(
                SessionModel.status == "completed",
                SessionModel.status == "COMPLETED"
            )
        )
        .count()
    )


def get_user_name(
    db: Session,
    user_id: int
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )
    return user.name if user else f"User #{user_id}"


def get_feedback_count(
    db: Session,
    user_id: int
):
    return (
        db.query(Feedback)
        .filter(Feedback.reviewee_id == user_id)
        .count()
    )


def has_availability(
    db: Session,
    mentor_id: int
):
    return (
        db.query(MentorAvailability)
        .filter(MentorAvailability.mentor_id == mentor_id)
        .first()
        is not None
    )