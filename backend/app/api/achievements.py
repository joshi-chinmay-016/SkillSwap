from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import logging

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.schemas.achievement_schema import (
    AchievementResponse,
    AchievementProgressResponse
)
from app.services.achievement_service import (
    get_user_achievement_responses,
    get_user_achievements_overview
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/achievements",
    tags=["Achievements"]
)


@router.get(
    "",
    response_model=List[AchievementResponse]
)
def get_my_achievements(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retrieves all master achievements along with unlock status and timestamps for the authenticated user.
    Never accepts user_id as a query parameter to preserve strict authorization boundaries.
    """
    try:
        responses, _, _ = get_user_achievement_responses(db, current_user.id)
        return responses
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving achievements for user_id={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while fetching achievements"
        )
    except Exception as e:
        logger.error(f"Unexpected error while retrieving achievements for user_id={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve achievements"
        )


@router.get(
    "/progress",
    response_model=AchievementProgressResponse
)
def get_my_achievement_progress(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retrieves achievement progress, XP metrics, Level info, and unlock summary for the authenticated user.
    """
    try:
        return get_user_achievements_overview(db, current_user.id)
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving achievement progress for user_id={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while fetching achievement progress"
        )
    except Exception as e:
        logger.error(f"Unexpected error while retrieving achievement progress for user_id={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve achievement progress"
        )
