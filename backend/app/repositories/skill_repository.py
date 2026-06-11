from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.models.user_skill import UserSkill


def get_all_skills(
    db: Session
):

    return db.query(
        Skill
    ).all()


def create_skill(
    db: Session,
    skill: Skill
):

    db.add(skill)

    db.commit()

    db.refresh(skill)

    return skill


def add_user_skill(
    db: Session,
    user_skill: UserSkill
):

    db.add(user_skill)

    db.commit()

    db.refresh(user_skill)

    return user_skill


def get_user_skills(
    db: Session,
    user_id: int
):

    return (
        db.query(UserSkill)
        .filter(
            UserSkill.user_id == user_id
        )
        .all()
    )