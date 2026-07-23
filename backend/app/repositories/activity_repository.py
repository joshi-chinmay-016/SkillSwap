"""
Activity Repository module. Re-exports repository functions from learning_activity_repository.py.
"""
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
    get_user_activity_totals,
)

__all__ = [
    "create_learning_activity",
    "get_user_activities",
    "get_user_heatmap_data",
    "get_user_distinct_activity_dates",
    "get_user_weekly_activity_counts",
    "get_user_monthly_activity_counts",
    "get_user_activity_distribution_counts",
    "get_user_recent_period_activity_counts",
    "get_user_activity_count_in_days",
    "get_user_activity_totals",
]
