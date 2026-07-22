import logging
import time
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional, Dict, Any, List
logger = logging.getLogger(__name__)
from app.repositories.learning_activity_repository import (
    create_learning_activity,
    get_user_activities,
    get_user_heatmap_data,
    get_user_distinct_activity_dates
)
from app.schemas.learning_activity import (
    HeatmapActivityItem,
    HeatmapResponse,
    StreakResponse,
    MilestoneInfo
)

STREAK_MILESTONES = [
    {"name": "Getting Started", "threshold": 3},
    {"name": "Consistent Learner", "threshold": 7},
    {"name": "Momentum Builder", "threshold": 15},
    {"name": "Dedicated Learner", "threshold": 30},
    {"name": "Learning Machine", "threshold": 60},
    {"name": "Century Streak", "threshold": 100},
    {"name": "Legendary Learner", "threshold": 365},
]


def get_milestone_progress(current_streak: int) -> tuple[Optional[MilestoneInfo], Optional[MilestoneInfo], int, float]:
    """
    Computes current milestone, next milestone, remaining days, and progress percentage.
    """
    current_m = None
    next_m = None

    for m in STREAK_MILESTONES:
        if current_streak >= m["threshold"]:
            current_m = m
        elif next_m is None:
            next_m = m

    if next_m is None:
        # Achieved or exceeded highest milestone (e.g. 365+)
        remaining_days = 0
        progress_percentage = 100.0
    else:
        remaining_days = next_m["threshold"] - current_streak
        current_threshold = current_m["threshold"] if current_m else 0
        next_threshold = next_m["threshold"]

        range_span = next_threshold - current_threshold
        gained = current_streak - current_threshold
        progress_percentage = round((gained / range_span) * 100.0, 1)

    cur_info = MilestoneInfo(name=current_m["name"], threshold=current_m["threshold"]) if current_m else None
    nxt_info = MilestoneInfo(name=next_m["name"], threshold=next_m["threshold"]) if next_m else None

    return cur_info, nxt_info, remaining_days, progress_percentage


def get_user_learning_streak(
    db: Session,
    user_id: int,
    ref_today: Optional[date] = None
) -> StreakResponse:
    """
    Computes learning streak analytics for an authenticated user.
    Strictly read-only; derives statistics directly from LearningActivity records.
    Logs authenticated user ID, execution time, current streak, and longest streak.
    """
    start_time = time.perf_counter()
    today = ref_today if ref_today is not None else date.today()

    distinct_dates = get_user_distinct_activity_dates(db, user_id)

    if not distinct_dates:
        cur_m, nxt_m, rem_days, prog_pct = get_milestone_progress(0)
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Streak calculated for user_id={user_id} in {execution_time_ms:.2f}ms: "
            f"current_streak=0, longest_streak=0, total_active_days=0, consistency_score=0.0."
        )
        return StreakResponse(
            current_streak=0,
            longest_streak=0,
            total_active_days=0,
            last_active_date=None,
            consistency_score=0.0,
            current_milestone=cur_m,
            next_milestone=nxt_m,
            remaining_days=rem_days,
            progress_percentage=prog_pct
        )

    total_active_days = len(distinct_dates)
    last_active_date = str(distinct_dates[-1])

    # 1. Compute Longest Streak
    longest_streak = 0
    current_run = 0
    prev_date = None

    for d in distinct_dates:
        if prev_date is None:
            current_run = 1
        elif d == prev_date + timedelta(days=1):
            current_run += 1
        else:
            current_run = 1

        if current_run > longest_streak:
            longest_streak = current_run

        prev_date = d

    # 2. Compute Current Streak
    yesterday = today - timedelta(days=1)
    active_dates_set = set(distinct_dates)

    if today not in active_dates_set and yesterday not in active_dates_set:
        current_streak = 0
    else:
        current_streak = 0
        check_date = today if today in active_dates_set else yesterday
        while check_date in active_dates_set:
            current_streak += 1
            check_date -= timedelta(days=1)

    # 3. Compute Consistency Score
    first_activity_date = distinct_dates[0]
    days_since_first = (today - first_activity_date).days + 1
    if days_since_first < 1:
        days_since_first = 1

    raw_consistency = (total_active_days / days_since_first) * 100.0
    consistency_score = round(min(100.0, max(0.0, raw_consistency)), 1)

    # 4. Compute Milestone Progress
    cur_m, nxt_m, rem_days, prog_pct = get_milestone_progress(current_streak)

    execution_time_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"Streak calculated for user_id={user_id} in {execution_time_ms:.2f}ms: "
        f"current_streak={current_streak}, longest_streak={longest_streak}, "
        f"total_active_days={total_active_days}, consistency_score={consistency_score}%."
    )

    return StreakResponse(
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_active_days=total_active_days,
        last_active_date=last_active_date,
        consistency_score=consistency_score,
        current_milestone=cur_m,
        next_milestone=nxt_m,
        remaining_days=rem_days,
        progress_percentage=prog_pct
    )

from typing import Optional, Dict, Any, List




def record_learning_activity(
    db: Session,
    user_id: int,
    activity_type: str,
    entity_type: str,
    entity_id: int,
    activity_data: Optional[dict] = None
):
    return create_learning_activity(
        db,
        user_id,
        activity_type,
        entity_type,
        entity_id,
        activity_data
    )


def get_user_activity_history(
    db: Session,
    user_id: int,
    page: int = 1,
    size: int = 20,
    activity_type: Optional[str] = None
):
    return get_user_activities(
        db,
        user_id,
        page,
        size,
        activity_type
    )


def get_user_activity_heatmap(
    db: Session,
    user_id: int
) -> HeatmapResponse:
    """
    Computes aggregated learning activity heatmap DTO for an authenticated user.
    Reads pre-aggregated SQL daily counts without modifying data.
    Logs authenticated user ID, execution time, number of active days, and total activities.
    """
    start_time = time.perf_counter()

    raw_data = get_user_heatmap_data(db, user_id)

    if not raw_data:
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Heatmap generated for user_id={user_id} in {execution_time_ms:.2f}ms: 0 active days, 0 total activities."
        )
        return HeatmapResponse(
            start_date=None,
            end_date=None,
            total_active_days=0,
            total_activities=0,
            activity=[]
        )

    activity_items = [
        HeatmapActivityItem(date=item["date"], count=item["count"])
        for item in raw_data
    ]

    total_activities = sum(item["count"] for item in raw_data)
    total_active_days = len(raw_data)
    start_date = raw_data[0]["date"]
    end_date = raw_data[-1]["date"]

    execution_time_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"Heatmap generated for user_id={user_id} in {execution_time_ms:.2f}ms: "
        f"{total_active_days} active days, {total_activities} total activities."
    )

    return HeatmapResponse(
        start_date=start_date,
        end_date=end_date,
        total_active_days=total_active_days,
        total_activities=total_activities,
        activity=activity_items
    )






