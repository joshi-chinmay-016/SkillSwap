from sqlalchemy.orm import Session

from app.models.user_skill import UserSkill


def get_teachers(
    db: Session,
    skill_id: int
):

    return (
        db.query(UserSkill)
        .filter(
            UserSkill.skill_id == skill_id,
            UserSkill.type == "teach"
        )
        .all()
    )


def get_learners(
    db: Session,
    skill_id: int
):

    return (
        db.query(UserSkill)
        .filter(
            UserSkill.skill_id == skill_id,
            UserSkill.type == "learn"
        )
        .all()
    )