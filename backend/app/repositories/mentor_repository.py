from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.user import User
from app.models.user_skill import UserSkill
from app.models.skill import Skill


def get_teaching_users(
    db: Session,
    exclude_user_id: Optional[int] = None
) -> List[User]:
    query = (
        db.query(User)
        .join(UserSkill, User.id == UserSkill.user_id)
        .filter(func.lower(UserSkill.type) == "teach")
    )
    if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    return query.order_by(User.id.desc()).distinct().all()


def get_teaching_users_by_skill(
    db: Session,
    skill_name: str,
    exclude_user_id: Optional[int] = None
) -> List[User]:
    clean_skill = skill_name.strip().lower() if skill_name else ""
    query = (
        db.query(User)
        .join(UserSkill, User.id == UserSkill.user_id)
        .join(UserSkill.skill)
        .filter(func.lower(UserSkill.type) == "teach")
        .filter(func.lower(Skill.name).ilike(f"%{clean_skill}%"))
    )
    if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    return query.order_by(User.id.desc()).distinct().all()