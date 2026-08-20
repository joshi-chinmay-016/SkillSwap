from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.models.user_skill import UserSkill

from app.repositories.skill_repository import (
    get_all_skills,
    create_skill,
    add_user_skill,
    get_user_skills
)


def list_skills(
    db: Session
):

    return get_all_skills(
        db
    )


def create_new_skill(
    db: Session,
    name: str,
    category: str,
    description: str | None
):

    skill = Skill(
        name=name,
        category=category,
        description=description
    )

    return create_skill(
        db,
        skill
    )


def assign_skill_to_user(
    db: Session,
    user_id: int,
    skill_id: int,
    skill_type: str
):

    user_skill = UserSkill(
        user_id=user_id,
        skill_id=skill_id,
        type=skill_type,
        verification_status="CLAIMED"
    )

    return add_user_skill(
        db,
        user_skill
    )



def list_user_skills(
    db: Session,
    user_id: int
):

    return get_user_skills(
        db,
        user_id
    )