from sqlalchemy.orm import Session, selectinload
from app.models.journey import LearningJourney, JourneyMilestone, JourneyTask
from typing import List, Optional
from datetime import datetime

def get_learning_journey_by_id(db: Session, journey_id: int) -> Optional[LearningJourney]:
    return (
        db.query(LearningJourney)
        .options(
            selectinload(LearningJourney.milestones)
            .selectinload(JourneyMilestone.tasks)
        )
        .filter(LearningJourney.id == journey_id)
        .first()
    )

def get_active_learning_journey_by_user(db: Session, user_id: int) -> Optional[LearningJourney]:
    return (
        db.query(LearningJourney)
        .options(
            selectinload(LearningJourney.milestones)
            .selectinload(JourneyMilestone.tasks)
        )
        .filter(
            LearningJourney.user_id == user_id,
            LearningJourney.status == "active"
        )
        .order_by(LearningJourney.created_at.desc())
        .first()
    )

def get_all_learning_journeys_by_user(db: Session, user_id: int) -> List[LearningJourney]:
    return (
        db.query(LearningJourney)
        .options(
            selectinload(LearningJourney.milestones)
            .selectinload(JourneyMilestone.tasks)
        )
        .filter(LearningJourney.user_id == user_id)
        .order_by(LearningJourney.created_at.desc())
        .all()
    )

def get_task_by_id(db: Session, task_id: int) -> Optional[JourneyTask]:
    return (
        db.query(JourneyTask)
        .filter(JourneyTask.id == task_id)
        .first()
    )

def save_learning_journey(db: Session, journey: LearningJourney) -> LearningJourney:
    db.add(journey)
    db.commit()
    db.refresh(journey)
    return journey

def update_learning_journey(db: Session, journey: LearningJourney) -> LearningJourney:
    db.commit()
    db.refresh(journey)
    return journey
