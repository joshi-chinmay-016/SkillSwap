from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.models.journey import LearningJourney, JourneyMilestone, JourneyTask
from app.schemas.journey import LearningJourneyCreate, LearningJourneyUpdate
from app.repositories.journey_repository import (
    get_learning_journey_by_id,
    get_active_learning_journey_by_user,
    get_all_learning_journeys_by_user,
    update_learning_journey
)

def create_journey(db: Session, user_id: int, journey_data: LearningJourneyCreate) -> LearningJourney:
    try:
        # Pause any existing active journeys to avoid conflicts
        existing_active = (
            db.query(LearningJourney)
            .filter(
                LearningJourney.user_id == user_id,
                LearningJourney.status == "active"
            )
            .all()
        )
        for old_journey in existing_active:
            old_journey.status = "paused"
            
        db_journey = LearningJourney(
            user_id=user_id,
            title=journey_data.title,
            target_role=journey_data.target_role,
            description=journey_data.description,
            duration_months=journey_data.duration_months,
            total_weeks=len(journey_data.weeks),
            status="active",
            progress_percentage=0.0,
            current_week=1
        )
        db.add(db_journey)
        db.flush() # get id
        
        for w in journey_data.weeks:
            db_milestone = JourneyMilestone(
                journey_id=db_journey.id,
                week_number=w.week,
                topic=w.topic,
                goal=w.goal,
                status="pending"
            )
            db.add(db_milestone)
            db.flush()  # get milestone id

            # Persist tasks if any
            for t in getattr(w, "tasks", []):
                db_task = JourneyTask(
                    milestone_id=db_milestone.id,
                    title=t.title,
                    description=t.description
                )
                db.add(db_task)
            
        db.commit()
        db.refresh(db_journey)
        return db_journey
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create learning journey: {str(e)}"
        )

def get_my_journeys(db: Session, user_id: int) -> List[LearningJourney]:
    return get_all_learning_journeys_by_user(db, user_id)

def get_active_journey(db: Session, user_id: int) -> Optional[LearningJourney]:
    return get_active_learning_journey_by_user(db, user_id)

def get_journey_by_id_and_user(db: Session, journey_id: int, user_id: int) -> LearningJourney:
    journey = get_learning_journey_by_id(db, journey_id)
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning journey not found"
        )
    if journey.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this learning journey"
        )
    return journey

def update_journey(db: Session, journey_id: int, user_id: int, update_data: LearningJourneyUpdate) -> LearningJourney:
    journey = get_journey_by_id_and_user(db, journey_id, user_id)
    
    if update_data.title is not None:
        journey.title = update_data.title
    if update_data.description is not None:
        journey.description = update_data.description
    if update_data.duration_months is not None:
        journey.duration_months = update_data.duration_months
    if update_data.current_week is not None:
        journey.current_week = update_data.current_week
        
    if update_data.status is not None:
        new_status = update_data.status.lower()
        if new_status not in ["active", "paused", "completed", "archived"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid journey status. Permitted statuses: active, paused, completed, archived"
            )
        
        # If transitioning to active, pause other active journeys
        if new_status == "active" and journey.status != "active":
            existing_active = (
                db.query(LearningJourney)
                .filter(
                    LearningJourney.user_id == user_id,
                    LearningJourney.status == "active",
                    LearningJourney.id != journey_id
                )
                .all()
            )
            for old_journey in existing_active:
                old_journey.status = "paused"
                
        journey.status = new_status
        
    return update_learning_journey(db, journey)

def archive_journey(db: Session, journey_id: int, user_id: int) -> LearningJourney:
    journey = get_journey_by_id_and_user(db, journey_id, user_id)
    journey.status = "archived"
    return update_learning_journey(db, journey)
