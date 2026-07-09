from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

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
        .options(joinedload(UserSkill.skill))
        .filter(
            UserSkill.user_id == user_id
        )
        .all()
    )

def get_skill_by_id(
    db,
    skill_id: int
):
    return (
        db.query(Skill)
        .filter(
            Skill.id == skill_id
        )
        .first()
    )

def remove_user_skill(
    db: Session,
    user_skill_id: int,
    user_id: int
):
    user_skill = (
        db.query(UserSkill)
        .filter(
            UserSkill.id == user_skill_id,
            UserSkill.user_id == user_id
        )
        .first()
    )
    if user_skill:
        db.delete(user_skill)
        db.commit()
    return user_skill