"""
SkillSwap Arena — Teaching & Learning Capability Service (Phase 8.2)

Enforces the core product principle:
- Mentor and Learner are contextual capabilities, NOT static RBAC account roles.
- Any user can learn skills while simultaneously teaching verified skills.
- Sessions assign contextual roles per session (mentor vs learner).
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.user_skill import UserSkill
from app.models.skill import Skill
from app.models.session import Session as SessionModel


def get_user_capabilities(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Computes real-time contextual capabilities and session history for a user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    user_skills = (
        db.query(UserSkill, Skill)
        .join(Skill, UserSkill.skill_id == Skill.id)
        .filter(UserSkill.user_id == user_id)
        .all()
    )

    verified_teaching = []
    pending_teaching = []
    learning_skills = []

    for us, skill in user_skills:
        skill_type = (us.type or "").upper()
        v_status = (us.verification_status or "CLAIMED").upper()

        if skill_type == "TEACH":
            if v_status == "VERIFIED":
                verified_teaching.append({
                    "skill_id": skill.id,
                    "skill_name": skill.name,
                    "verification_status": "VERIFIED",
                    "score": us.score,
                    "verified_at": us.verified_at.isoformat() if us.verified_at else None,
                })
            else:
                pending_teaching.append({
                    "skill_id": skill.id,
                    "skill_name": skill.name,
                    "verification_status": v_status,
                    "claimed_at": us.claimed_at.isoformat() if us.claimed_at else None,
                })
        elif skill_type == "LEARN":
            learning_skills.append({
                "skill_id": skill.id,
                "skill_name": skill.name,
            })

    # Query real session counts for contextual mentor / learner roles
    mentor_sessions_count = (
        db.query(func.count(SessionModel.id))
        .filter(SessionModel.mentor_id == user_id)
        .scalar()
        or 0
    )

    learner_sessions_count = (
        db.query(func.count(SessionModel.id))
        .filter(SessionModel.requester_id == user_id)
        .scalar()
        or 0
    )

    return {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": getattr(user, "role", "USER"),
        "is_active": getattr(user, "is_active", True),
        "can_teach": len(verified_teaching) > 0,
        "can_learn": getattr(user, "is_active", True),
        "verified_teaching_skills": verified_teaching,
        "pending_teaching_skills": pending_teaching,
        "learning_skills": learning_skills,
        "session_history": {
            "as_mentor_count": mentor_sessions_count,
            "as_learner_count": learner_sessions_count,
            "total_sessions": mentor_sessions_count + learner_sessions_count,
        }
    }


def is_verified_to_teach(db: Session, user_id: int, skill_id: int) -> bool:
    """
    Checks if a user is verified to teach a specific skill.
    """
    record = (
        db.query(UserSkill)
        .filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill_id,
            UserSkill.type == "TEACH",
            UserSkill.verification_status == "VERIFIED"
        )
        .first()
    )
    return record is not None
