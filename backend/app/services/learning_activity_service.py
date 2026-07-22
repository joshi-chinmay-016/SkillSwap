import logging
import time
from sqlalchemy.orm import Session
from app.repositories.learning_activity_repository import (
    create_learning_activity,
    get_user_activities,
    get_user_heatmap_data
)
from app.schemas.learning_activity import (
    HeatmapActivityItem,
    HeatmapResponse
)
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


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


