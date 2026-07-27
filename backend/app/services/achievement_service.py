import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple, Any

from app.models.learning_activity import LearningActivity
from app.models.achievement import Achievement
from app.repositories.achievement_repository import (
    get_all_achievements,
    get_user_unlocked_map
)
from app.schemas.achievement_schema import (
    BadgeDTO,
    AchievementResponse,
    LevelResponse,
    AchievementProgressResponse
)
from app.services.achievement_engine import get_user_metrics

logger = logging.getLogger(__name__)

# Configurable Activity XP values
ACTIVITY_XP_MAP = {
    "session_completed": 10,
    "session": 10,
    "journey_completed": 50,
    "journey": 50,
    "milestone_completed": 30,
    "milestone": 30,
    "quiz_completed": 20,
    "task_completed": 20,
    "task": 20,
}
DEFAULT_ACTIVITY_XP = 10

# Level thresholds: Level 1 (0), Level 2 (100), Level 3 (250), Level 4 (450), Level 5 (700)
LEVEL_THRESHOLDS = [0, 100, 250, 450, 700]


def get_level_threshold(level: int) -> int:
    """
    Returns XP threshold required to reach a specific level.
    Uses configurable progression array and formula for levels beyond defined list.
    """
    if level <= 1:
        return 0
    idx = level - 1
    if idx < len(LEVEL_THRESHOLDS):
        return LEVEL_THRESHOLDS[idx]
    # For levels beyond 5: Level N threshold = Level 5 threshold + sum of increments
    last_defined = LEVEL_THRESHOLDS[-1]
    extra_levels = level - len(LEVEL_THRESHOLDS)
    # Increment grows by 50 per level beyond level 5 (300 + 50 * k)
    extra_xp = sum(300 + 50 * k for k in range(extra_levels))
    return last_defined + extra_xp


def calculate_user_level(current_xp: int) -> LevelResponse:
    """
    Calculates current level, current XP, next level, XP needed to reach next level, and progress percentage.
    """
    level = 1
    while True:
        next_threshold = get_level_threshold(level + 1)
        if current_xp >= next_threshold:
            level += 1
        else:
            break

    curr_threshold = get_level_threshold(level)
    next_threshold = get_level_threshold(level + 1)

    xp_in_level = current_xp - curr_threshold
    span = next_threshold - curr_threshold

    xp_to_next = next_threshold - current_xp
    progress_pct = round((xp_in_level / span) * 100.0, 1) if span > 0 else 100.0
    progress_pct = min(100.0, max(0.0, progress_pct))

    return LevelResponse(
        current_level=level,
        current_xp=current_xp,
        next_level=level + 1,
        xp_to_next_level=xp_to_next,
        progress_percentage=progress_pct
    )


def calculate_total_xp(db: Session, user_id: int, unlocked_map: Dict[int, Any], all_achievements: List[Achievement]) -> int:
    """
    Calculates total XP earned from LearningActivities + Unlocked Achievement rewards.
    Strictly derived from activity logs without duplicating XP records.
    """
    activities = db.query(LearningActivity.activity_type).filter(LearningActivity.user_id == user_id).all()

    activity_xp = 0
    for act in activities:
        act_key = act.activity_type.lower().replace(" ", "_")
        activity_xp += ACTIVITY_XP_MAP.get(act_key, DEFAULT_ACTIVITY_XP)

    achievement_xp = 0
    ach_map = {a.id: a.xp_reward for a in all_achievements}
    for ach_id in unlocked_map.keys():
        achievement_xp += ach_map.get(ach_id, 50)

    return activity_xp + achievement_xp


def get_user_achievement_responses(db: Session, user_id: int) -> Tuple[List[AchievementResponse], int, int]:
    """
    Builds achievement response list for a user including unlock status and progress.
    Merges master achievements with user unlock records using minimal queries.
    """
    all_achievements = get_all_achievements(db)
    unlocked_map = get_user_unlocked_map(db, user_id)
    metrics = get_user_metrics(db, user_id)

    responses: List[AchievementResponse] = []
    unlocked_count = 0

    for ach in all_achievements:
        is_unlocked = ach.id in unlocked_map
        unlocked_at = unlocked_map.get(ach.id)

        if is_unlocked:
            unlocked_count += 1
            current_val = ach.requirement_value
            progress_pct = 100.0
        else:
            req_type = ach.requirement_type.lower()
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
                current_val = metrics["activity_count"]

            current_val = min(current_val, ach.requirement_value)
            progress_pct = round((current_val / ach.requirement_value) * 100.0, 1) if ach.requirement_value > 0 else 100.0
            progress_pct = min(100.0, max(0.0, progress_pct))

        badge = BadgeDTO(
            name=ach.badge_name,
            icon=ach.icon,
            tier=ach.badge_tier
        )

        responses.append(
            AchievementResponse(
                id=ach.id,
                name=ach.name,
                description=ach.description,
                category=ach.category,
                badge=badge,
                icon=ach.icon,
                unlocked=is_unlocked,
                unlocked_at=unlocked_at,
                xp_reward=ach.xp_reward,
                current_value=current_val,
                target_value=ach.requirement_value,
                progress_percentage=progress_pct
            )
        )

    return responses, unlocked_count, len(all_achievements)


def get_user_achievements_overview(db: Session, user_id: int) -> AchievementProgressResponse:
    """
    Generates complete achievement progress, XP, level, and achievement list response.
    """
    all_achievements = get_all_achievements(db)
    unlocked_map = get_user_unlocked_map(db, user_id)

    total_xp = calculate_total_xp(db, user_id, unlocked_map, all_achievements)
    level_info = calculate_user_level(total_xp)

    achievements, unlocked_count, total_count = get_user_achievement_responses(db, user_id)

    return AchievementProgressResponse(
        level=level_info,
        unlocked_count=unlocked_count,
        total_count=total_count,
        achievements=achievements
    )
