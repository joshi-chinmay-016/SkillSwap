from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class JourneyTaskResponse(BaseModel):
    id: int
    milestone_id: int
    title: str
    description: Optional[str] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JourneyMilestoneResponse(BaseModel):
    id: int
    journey_id: int
    week_number: int
    topic: str
    goal: str
    status: str
    created_at: datetime
    updated_at: datetime
    tasks: List[JourneyTaskResponse] = []

    class Config:
        from_attributes = True


class LearningJourneyResponse(BaseModel):
    id: int
    user_id: int
    title: str
    target_role: str
    description: Optional[str] = None
    duration_months: Optional[int] = None
    status: str
    progress_percentage: float
    current_week: int
    total_weeks: int
    created_at: datetime
    updated_at: datetime
    milestones: List[JourneyMilestoneResponse] = []

    class Config:
        from_attributes = True


class JourneyTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    resources: Optional[List[str]] = None


class JourneyMilestoneCreate(BaseModel):
    week: int
    topic: str
    goal: str
    tasks: List[JourneyTaskCreate] = []


class LearningJourneyCreate(BaseModel):
    title: str
    target_role: str
    description: Optional[str] = None
    duration_months: Optional[int] = None
    weeks: List[JourneyMilestoneCreate]


class LearningJourneyUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    duration_months: Optional[int] = None
    current_week: Optional[int] = None
