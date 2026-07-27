from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.learning_activity import LearningActivity
from typing import List, Optional
from datetime import datetime, date, timedelta


def create_learning_activity(
    db: Session,
    user_id: int,
    activity_type: str,
    entity_type: str,
    entity_id: int,
    activity_data: Optional[dict] = None
) -> LearningActivity:
    activity = LearningActivity(
        user_id=user_id,
        activity_type=activity_type,
        entity_type=entity_type,
        entity_id=entity_id,
        activity_data=activity_data
    )
    db.add(activity)
    db.flush()
    return activity


def get_user_activities(
    db: Session,
    user_id: int,
    page: int = 1,
    size: int = 20,
    activity_type: Optional[str] = None
) -> tuple[List[LearningActivity], int]:
    query = db.query(LearningActivity).filter(
        LearningActivity.user_id == user_id
    )

    if activity_type:
        query = query.filter(LearningActivity.activity_type == activity_type)

    total = query.count()

    activities = (
        query
        .order_by(LearningActivity.created_at.desc(), LearningActivity.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return activities, total


def get_user_heatmap_data(
    db: Session,
    user_id: int
) -> List[dict]:
    date_col = func.date(LearningActivity.created_at)
    results = (
        db.query(
            date_col.label("date"),
            func.count().label("count")
        )
        .filter(LearningActivity.user_id == user_id)
        .group_by(date_col)
        .order_by(date_col.asc())
        .all()
    )

    return [
        {
            "date": str(row.date),
            "count": int(row.count)
        }
        for row in results
    ]


def get_user_distinct_activity_dates(
    db: Session,
    user_id: int
) -> List[date]:
    """
    Retrieves distinct activity dates for the given user ordered chronologically ascending.
    """
    date_col = func.date(LearningActivity.created_at)
    results = (
        db.query(date_col.label("date"))
        .filter(LearningActivity.user_id == user_id)
        .group_by(date_col)
        .order_by(date_col.asc())
        .all()
    )

    distinct_dates = []
    for row in results:
        d = row.date
        if isinstance(d, str):
            d = datetime.strptime(d, "%Y-%m-%d").date()
        elif isinstance(d, datetime):
            d = d.date()
        if d and d not in distinct_dates:
            distinct_dates.append(d)

    return distinct_dates


def get_user_weekly_activity_counts(
    db: Session,
    user_id: int
) -> List[tuple[int, int]]:
    """
    Retrieves weekly activity counts for the given user, grouped by day of week (SQL DOW: 0=Sun, 1=Mon, ..., 6=Sat).
    Returns raw aggregated (dow_integer, count) tuples.
    """
    dow_col = func.extract('dow', LearningActivity.created_at)
    results = (
        db.query(
            dow_col.label("dow"),
            func.count().label("count")
        )
        .filter(LearningActivity.user_id == user_id)
        .group_by(dow_col)
        .all()
    )

    counts = []
    for row in results:
        if row.dow is not None:
            counts.append((int(row.dow), int(row.count)))
    return counts


def get_user_monthly_activity_counts(
    db: Session,
    user_id: int
) -> List[tuple[int, int]]:
    """
    Retrieves monthly activity counts for the given user, grouped by month integer (SQL MONTH: 1..12).
    Returns raw aggregated (month_integer, count) tuples.
    """
    month_col = func.extract('month', LearningActivity.created_at)
    results = (
        db.query(
            month_col.label("month"),
            func.count().label("count")
        )
        .filter(LearningActivity.user_id == user_id)
        .group_by(month_col)
        .order_by(month_col.asc())
        .all()
    )

    counts = []
    for row in results:
        if row.month is not None:
            counts.append((int(row.month), int(row.count)))
    return counts


def get_user_activity_distribution_counts(
    db: Session,
    user_id: int
) -> List[tuple[str, int]]:
    """
    Retrieves activity counts for the given user, grouped by activity_type string.
    Returns raw aggregated (activity_type, count) tuples.
    """
    results = (
        db.query(
            LearningActivity.activity_type.label("activity_type"),
            func.count().label("count")
        )
        .filter(LearningActivity.user_id == user_id)
        .group_by(LearningActivity.activity_type)
        .all()
    )

    counts = []
    for row in results:
        if row.activity_type is not None:
            counts.append((str(row.activity_type), int(row.count)))
    return counts


def get_user_recent_period_activity_counts(
    db: Session,
    user_id: int,
    ref_date: Optional[date] = None
) -> tuple[int, int]:
    """
    Retrieves activity counts for current 7-day period vs previous 7-day period (days 8-14 ago).
    Returns (curr_count, prev_count).
    """
    today = ref_date if ref_date is not None else date.today()

    start_curr_date = today - timedelta(days=6)
    start_curr_dt = datetime(start_curr_date.year, start_curr_date.month, start_curr_date.day, 0, 0, 0)
    end_curr_dt = datetime(today.year, today.month, today.day, 23, 59, 59, 999999)

    start_prev_date = today - timedelta(days=13)
    start_prev_dt = datetime(start_prev_date.year, start_prev_date.month, start_prev_date.day, 0, 0, 0)

    curr_count = (
        db.query(func.count(LearningActivity.id))
        .filter(
            LearningActivity.user_id == user_id,
            LearningActivity.created_at >= start_curr_dt,
            LearningActivity.created_at <= end_curr_dt
        )
        .scalar() or 0
    )

    prev_count = (
        db.query(func.count(LearningActivity.id))
        .filter(
            LearningActivity.user_id == user_id,
            LearningActivity.created_at >= start_prev_dt,
            LearningActivity.created_at < start_curr_dt
        )
        .scalar() or 0
    )

    return int(curr_count), int(prev_count)


def get_user_activity_count_in_days(
    db: Session,
    user_id: int,
    days: int = 30,
    ref_date: Optional[date] = None
) -> int:
    """
    Retrieves total activity count for the last `days` period up to ref_date.
    """
    today = ref_date if ref_date is not None else date.today()
    start_date = today - timedelta(days=days - 1)
    start_dt = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
    end_dt = datetime(today.year, today.month, today.day, 23, 59, 59, 999999)

    count = (
        db.query(func.count(LearningActivity.id))
        .filter(
            LearningActivity.user_id == user_id,
            LearningActivity.created_at >= start_dt,
            LearningActivity.created_at <= end_dt
        )
        .scalar() or 0
    )
    return int(count)


def get_user_activity_totals(
    db: Session,
    user_id: int
) -> tuple[int, int]:
    """
    Retrieves total activity count and total distinct active days count for a given user.
    Returns (total_activities, total_active_days).
    """
    total_activities = (
        db.query(func.count(LearningActivity.id))
        .filter(LearningActivity.user_id == user_id)
        .scalar() or 0
    )

    date_col = func.date(LearningActivity.created_at)
    total_active_days = (
        db.query(func.count(func.distinct(date_col)))
        .filter(LearningActivity.user_id == user_id)
        .scalar() or 0
    )

    return int(total_activities), int(total_active_days)




