from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.schemas.learning_activity import LearningActivityListResponse
from app.services.learning_activity_service import get_user_activity_history

router = APIRouter(
    prefix="/learning-activities",
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
