import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any
from datetime import datetime, timezone

from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement
from app.models.learning_activity import LearningActivity
from app.models.journey import LearningJourney
from app.repositories.achievement_repository import (
    get_all_achievements,
    get_user_unlocked_achievement_ids,
    create_user_achievement
)
from app.services.learning_activity_service import get_user_learning_streak

logger = logging.getLogger(__name__)


def get_user_metrics(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Aggregates user metrics for achievement evaluation strictly from user activity data.
    """
    total_activities = db.query(LearningActivity).filter(LearningActivity.user_id == user_id).count()

    session_activities = db.query(LearningActivity).filter(
        LearningActivity.user_id == user_id,
        LearningActivity.activity_type.in_(["Session Completed", "session_completed", "session"])
    ).count()

    milestone_activities = db.query(LearningActivity).filter(
        LearningActivity.user_id == user_id,
        LearningActivity.activity_type.in_(["Milestone Completed", "milestone_completed", "milestone"])
    ).count()

    journey_activities = db.query(LearningActivity).filter(
        LearningActivity.user_id == user_id,
        LearningActivity.activity_type.in_(["Journey Completed", "journey_completed", "journey"])
    ).count()

    # Journey count can also be checked against LearningJourney table status
    completed_journeys_db = db.query(LearningJourney).filter(
        LearningJourney.user_id == user_id,
        LearningJourney.status == "completed"
    ).count()

    total_journeys = max(journey_activities, completed_journeys_db)

    # Streak metrics
    streak_info = get_user_learning_streak(db, user_id)
    max_streak = max(streak_info.current_streak, streak_info.longest_streak)
    consistency = streak_info.consistency_score

    return {
        "activity_count": total_activities,
        "session_count": session_activities,
        "milestone_count": milestone_activities,
        "journey_count": total_journeys,
        "streak_days": max_streak,
        "consistency_score": int(consistency)
    }


def evaluate_user_achievements(db: Session, user_id: int) -> List[UserAchievement]:
    """
    Evaluates all locked achievements for a user and automatically unlocks any that meet requirements.
    Transaction-safe with duplicate prevention.
    """
    newly_unlocked: List[UserAchievement] = []

    try:
        all_achievements = get_all_achievements(db)
        if not all_achievements:
            return newly_unlocked

        unlocked_ids = set(get_user_unlocked_achievement_ids(db, user_id))
        metrics = get_user_metrics(db, user_id)

        for achievement in all_achievements:
            if achievement.id in unlocked_ids:
                continue

            req_type = achievement.requirement_type.lower()
            target_val = achievement.requirement_value

            current_val = 0
            if req_type in ["activity_count", "activities", "learning"]:
                current_val = metrics["activity_count"]
            elif req_type in ["streak_days", "streak"]:
                current_val = metrics["streak_days"]
            elif req_type in ["journey_count", "journey"]:
                current_val = metrics["journey_count"]
            elif req_type in ["consistency_score", "consistency"]:
                current_val = metrics["consistency_score"]
            elif req_type in ["session_count", "session", "participation"]:
                current_val = metrics["session_count"]
            elif req_type in ["milestone_count", "milestone"]:
                current_val = metrics["milestone_count"]
            else:
                # Default fallback to activity_count
                current_val = metrics["activity_count"]

            if current_val >= target_val:
                try:
                    with db.begin_nested():
                        user_ach = create_user_achievement(
                            db=db,
                            user_id=user_id,
                            achievement_id=achievement.id,
                            unlocked_at=datetime.now(timezone.utc)
                        )
                        newly_unlocked.append(user_ach)
                        unlocked_ids.add(achievement.id)
                        logger.info(f"Automatically unlocked achievement id={achievement.id} ({achievement.name}) for user_id={user_id}")
                except IntegrityError:
                    # Already unlocked in concurrent request
                    logger.warning(f"Achievement id={achievement.id} already unlocked for user_id={user_id}")
                    continue

        if newly_unlocked:
            db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error evaluating achievements for user_id={user_id}: {str(e)}", exc_info=True)

    return newly_unlocked
