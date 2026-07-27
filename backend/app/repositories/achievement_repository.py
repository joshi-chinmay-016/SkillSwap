from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timezone

from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement


def get_all_achievements(db: Session) -> List[Achievement]:
    """
    Retrieves all available master achievements sorted by category and id.
    """
    return db.query(Achievement).order_by(Achievement.category, Achievement.id).all()


def get_user_achievements(db: Session, user_id: int) -> List[UserAchievement]:
    """
    Retrieves all unlocked achievement records for a specific user.
    """
    return db.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()


def get_user_unlocked_map(db: Session, user_id: int) -> Dict[int, datetime]:
    """
    Retrieves a mapping of achievement_id -> unlocked_at for a specific user.
    Uses a single query to prevent N+1 queries.
    """
    records = db.query(UserAchievement.achievement_id, UserAchievement.unlocked_at)\
                .filter(UserAchievement.user_id == user_id).all()
    return {rec.achievement_id: rec.unlocked_at for rec in records}


def get_user_unlocked_achievement_ids(db: Session, user_id: int) -> List[int]:
    """
    Retrieves list of achievement_ids unlocked by a specific user.
    """
    records = db.query(UserAchievement.achievement_id)\
                .filter(UserAchievement.user_id == user_id).all()
    return [rec.achievement_id for rec in records]


def create_user_achievement(
    db: Session,
    user_id: int,
    achievement_id: int,
    unlocked_at: Optional[datetime] = None
) -> UserAchievement:
    """
    Creates and persists a UserAchievement record.
    """
    now = unlocked_at if unlocked_at else datetime.now(timezone.utc)
    user_ach = UserAchievement(
        user_id=user_id,
        achievement_id=achievement_id,
        unlocked_at=now
    )
    db.add(user_ach)
    db.flush()
    return user_ach
