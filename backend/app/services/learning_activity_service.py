import logging
import time
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
logger = logging.getLogger(__name__)
from app.repositories.learning_activity_repository import (
    create_learning_activity,
    get_user_activities,
    get_user_heatmap_data,
    get_user_distinct_activity_dates,
    get_user_weekly_activity_counts,
    get_user_monthly_activity_counts,
    get_user_activity_distribution_counts,
    get_user_recent_period_activity_counts,
    get_user_activity_count_in_days,
    get_user_activity_totals
)
from app.schemas.learning_activity import (
    HeatmapActivityItem,
    HeatmapResponse,
    StreakResponse,
    MilestoneInfo,
    AnalyticsResponse,
    LearningTrendInfo,
    MostActiveDayInfo,
    AnalyticsSummaryInfo
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




def invalidate_user_learning_cache(user_id: int):
    """
    Invalidates all Redis-cached analytics, heatmaps, and streak records for the user.
    Scoped strictly by user_id to prevent cross-user interference.
    """
    try:
        from app.infrastructure.redis import invalidate_user_learning_data
        invalidate_user_learning_data(user_id)
    except Exception as e:
        logger.debug(f"Redis cache invalidation for user {user_id} skipped: {e}")


def record_learning_activity(
    db: Session,
    user_id: int,
    activity_type: str,
    entity_type: str,
    entity_id: int,
    activity_data: Optional[dict] = None,
    created_at: Optional[datetime] = None
):
    activity = create_learning_activity(
        db,
        user_id,
        activity_type,
        entity_type,
        entity_id,
        activity_data,
        created_at=created_at
    )
    # Invalidate user-scoped cache immediately
    invalidate_user_learning_cache(user_id)

    try:
        from app.services.achievement_engine import evaluate_user_achievements
        evaluate_user_achievements(db, user_id)
    except Exception as e:
        logger.error(f"Achievement evaluation failed after activity creation for user_id={user_id}: {str(e)}")
    return activity


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
    user_id: int,
    timezone_str: str = "UTC"
) -> HeatmapResponse:
    """
    Computes aggregated learning activity heatmap DTO for an authenticated user in their timezone.
    Derives real data from persisted LearningActivity records.
    Logs authenticated user ID, execution time, number of active days, and total activities.
    """
    start_time = time.perf_counter()

    raw_data = get_user_heatmap_data(db, user_id, timezone_str=timezone_str)

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


WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DOW_MAP = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    0: "Sunday"
}

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
MONTH_MAP = {i + 1: month for i, month in enumerate(MONTHS)}

DEFAULT_ACTIVITY_TYPES = [
    "Task Completed",
    "Milestone Completed",
    "Journey Completed",
    "Session Completed"
]

ACTIVITY_TYPE_MAPPING = {
    "task_completed": "Task Completed",
    "task": "Task Completed",
    "milestone_completed": "Milestone Completed",
    "milestone": "Milestone Completed",
    "journey_completed": "Journey Completed",
    "journey": "Journey Completed",
    "session_completed": "Session Completed",
    "session": "Session Completed",
}


def get_user_learning_analytics(
    db: Session,
    user_id: int,
    ref_date: Optional[date] = None
) -> AnalyticsResponse:
    """
    Generates aggregated learning intelligence analytics for an authenticated user.
    Reads aggregated SQL query results without modifying data.
    Computes learning trend, velocity, most active day, average per day, and summary.
    Logs authenticated user ID and execution time.
    """
    start_time = time.perf_counter()

    # 1. Weekly Activity Aggregation
    weekly_raw = get_user_weekly_activity_counts(db, user_id)
    weekly_activity = {day: 0 for day in WEEKDAYS}
    for dow_int, count in weekly_raw:
        day_name = DOW_MAP.get(dow_int)
        if day_name in weekly_activity:
            weekly_activity[day_name] += count

    # 2. Monthly Activity Aggregation
    monthly_raw = get_user_monthly_activity_counts(db, user_id)
    monthly_activity = {month: 0 for month in MONTHS}
    for month_int, count in monthly_raw:
        month_name = MONTH_MAP.get(month_int)
        if month_name in monthly_activity:
            monthly_activity[month_name] += count

    # 3. Activity Distribution Aggregation
    dist_raw = get_user_activity_distribution_counts(db, user_id)
    activity_distribution = {act_type: 0 for act_type in DEFAULT_ACTIVITY_TYPES}
    for raw_type, count in dist_raw:
        mapped_label = ACTIVITY_TYPE_MAPPING.get(raw_type)
        if not mapped_label:
            mapped_label = raw_type.replace("_", " ").title()
        activity_distribution[mapped_label] = activity_distribution.get(mapped_label, 0) + count

    # 4. Learning Trend (Current Week vs Previous Week)
    curr_count, prev_count = get_user_recent_period_activity_counts(db, user_id, ref_date=ref_date)
    if prev_count == 0:
        if curr_count > 0:
            trend_percentage = 100.0
            trend_direction = "up"
        else:
            trend_percentage = 0.0
            trend_direction = "stable"
    else:
        if curr_count > prev_count:
            trend_percentage = round(((curr_count - prev_count) / prev_count) * 100.0, 1)
            trend_direction = "up"
        elif curr_count < prev_count:
            trend_percentage = round(((prev_count - curr_count) / prev_count) * 100.0, 1)
            trend_direction = "down"
        else:
            trend_percentage = 0.0
            trend_direction = "stable"

    learning_trend = LearningTrendInfo(
        percentage=trend_percentage,
        direction=trend_direction
    )

    # 5. Learning Velocity (Average activities per day over last 30 days)
    last_30_count = get_user_activity_count_in_days(db, user_id, days=30, ref_date=ref_date)
    learning_velocity = round(last_30_count / 30.0, 1)

    # 6. Most Active Day (Weekday with highest count, tie-breaking chronologically Monday..Sunday)
    best_day = None
    max_count = 0
    for day in WEEKDAYS:
        c = weekly_activity.get(day, 0)
        if c > max_count:
            max_count = c
            best_day = day

    most_active_day = MostActiveDayInfo(day=best_day, count=max_count) if max_count > 0 and best_day else None

    # 7. Totals, Average Per Active Day, and Analytics Summary
    total_activities, total_active_days = get_user_activity_totals(db, user_id)
    average_per_day = round(total_activities / total_active_days, 1) if total_active_days > 0 else 0.0

    streak_info = get_user_learning_streak(db, user_id, ref_today=ref_date)
    summary = AnalyticsSummaryInfo(
        total_activities=total_activities,
        total_active_days=total_active_days,
        average_per_day=average_per_day,
        current_streak=streak_info.current_streak,
        longest_streak=streak_info.longest_streak
    )

    execution_time_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"Advanced analytics calculated for user_id={user_id} in {execution_time_ms:.2f}ms: "
        f"trend={trend_direction} ({trend_percentage}%), velocity={learning_velocity}, "
        f"total_activities={total_activities}, streak={streak_info.current_streak}."
    )

    return AnalyticsResponse(
        weekly_activity=weekly_activity,
        monthly_activity=monthly_activity,
        activity_distribution=activity_distribution,
        learning_trend=learning_trend,
        learning_velocity=learning_velocity,
        most_active_day=most_active_day,
        average_per_day=average_per_day,
        summary=summary
    )








