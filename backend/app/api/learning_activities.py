from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
import logging

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.schemas.learning_activity import (
    LearningActivityListResponse,
    HeatmapResponse,
    StreakResponse
)
from app.services.learning_activity_service import (
    get_user_activity_history,
    get_user_activity_heatmap,
    get_user_learning_streak
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/learning-activities",
    tags=["Learning Activities"]
)

activities_router = APIRouter(
    prefix="/activities",
    tags=["Learning Activities"]
)


@router.get(
    "/me",
    response_model=LearningActivityListResponse
)
def get_my_activities(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    activity_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    activities, total = get_user_activity_history(
        db,
        current_user.id,
        page,
        size,
        activity_type
    )

    return LearningActivityListResponse(
        activities=activities,
        total=total,
        page=page,
        size=size
    )


@router.get(
    "/heatmap",
    response_model=HeatmapResponse
)
@activities_router.get(
    "/heatmap",
    response_model=HeatmapResponse
)
def get_heatmap(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        return get_user_activity_heatmap(db, current_user.id)
    except SQLAlchemyError as e:
        logger.error(f"Database error while generating heatmap for user_id={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while fetching activity heatmap"
        )
    except Exception as e:
        logger.error(f"Unexpected error while generating heatmap for user_id={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate learning activity heatmap"
        )


@router.get(
    "/streak",
    response_model=StreakResponse
)
@activities_router.get(
    "/streak",
    response_model=StreakResponse
)
def get_streak(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        return get_user_learning_streak(db, current_user.id)
    except SQLAlchemyError as e:
        logger.error(f"Database error while calculating streak for user_id={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while fetching learning streak"
        )
    except Exception as e:
        logger.error(f"Unexpected error while calculating streak for user_id={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate learning streak"
        )



