from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_skill import UserSkill


def get_teaching_users(
    db: Session
):
    return (
        db.query(User)
        .join(
            UserSkill,
            User.id == UserSkill.user_id
    )
        .filter(
            UserSkill.type == "teach"
        )
    .distinct()
    .limit(100)
    .all()
)


def get_teaching_users_by_skill(
    db: Session,
    skill_name: str
):

    return (
        db.query(
            User
        )
        .join(
            UserSkill,
            User.id == UserSkill.user_id
        )
        .join(
            UserSkill.skill
        )
        .filter(
            UserSkill.type == "teach"
        )
        .filter(
            UserSkill.skill.has(
                name=skill_name
            )
        )
        .distinct()
        .limit(100)
        .all()
    )