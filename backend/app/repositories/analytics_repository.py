from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.models.user_skill import UserSkill


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