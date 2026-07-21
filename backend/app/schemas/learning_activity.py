from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class LearningActivityResponse(BaseModel):
    id: int
    user_id: int
    activity_type: str
    entity_type: str
    entity_id: int
    activity_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LearningActivityListResponse(BaseModel):
    activities: list[LearningActivityResponse]
    total: int
    page: int
    size: int


class HeatmapActivityItem(BaseModel):
    date: str
    count: int


class HeatmapResponse(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_active_days: int = 0
    total_activities: int = 0
    activity: list[HeatmapActivityItem] = []


class MilestoneInfo(BaseModel):
    name: str
    threshold: int


class StreakResponse(BaseModel):
    current_streak: int = 0
    longest_streak: int = 0
    total_active_days: int = 0
    last_active_date: Optional[str] = None
    consistency_score: float = 0.0
    current_milestone: Optional[MilestoneInfo] = None
    next_milestone: Optional[MilestoneInfo] = None
    remaining_days: int = 0
    progress_percentage: float = 0.0



