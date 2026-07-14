from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.schemas.journey import (
    LearningJourneyCreate,
    LearningJourneyUpdate,
    LearningJourneyResponse,
    JourneyTaskResponse
)
from app.services import journey_service

router = APIRouter(
    prefix="/journeys",
    tags=["Learning Journeys"]
)


class TaskToggleRequest(BaseModel):
    is_completed: bool


@router.post(
    "",
    response_model=LearningJourneyResponse,
    status_code=status.HTTP_201_CREATED
)
def create_learning_journey(
    journey_data: LearningJourneyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return journey_service.create_journey(db, current_user.id, journey_data)


@router.get(
    "/me",
    response_model=List[LearningJourneyResponse]
)
def get_my_learning_journeys(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return journey_service.get_my_journeys(db, current_user.id)


@router.get(
    "/me/active",
    response_model=Optional[LearningJourneyResponse]
)
def get_active_learning_journey(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return journey_service.get_active_journey(db, current_user.id)


@router.get(
    "/{journey_id}",
    response_model=LearningJourneyResponse
)
def get_learning_journey(
    journey_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return journey_service.get_journey_by_id_and_user(db, journey_id, current_user.id)


@router.patch(
    "/{journey_id}",
    response_model=LearningJourneyResponse
)
def update_learning_journey(
    journey_id: int,
    update_data: LearningJourneyUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return journey_service.update_journey(db, journey_id, current_user.id, update_data)


@router.delete(
    "/{journey_id}",
    response_model=LearningJourneyResponse
)
def delete_learning_journey(
    journey_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return journey_service.archive_journey(db, journey_id, current_user.id)


@router.patch(
    "/tasks/{task_id}/toggle",
    response_model=JourneyTaskResponse
)
def toggle_task_completion(
    task_id: int,
    request: TaskToggleRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return journey_service.toggle_task_completion(
        db,
        task_id,
        current_user.id,
        request.is_completed
    )
