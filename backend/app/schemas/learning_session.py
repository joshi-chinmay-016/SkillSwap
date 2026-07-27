from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class LearningSessionCreate(BaseModel):
    """Schema for creating a new learning session."""
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Title of the learning session",
        json_schema_extra={"examples": ["Introduction to Python Basics"]}
    )


class LearningSessionUpdate(BaseModel):
    """Schema for updating a learning session."""
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated title of the learning session"
    )


class LearningSessionResponse(BaseModel):
    """Schema for a learning session response."""
    id: int
    uuid: str
    user_id: int
    journey_id: int
    title: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LearningSessionListResponse(BaseModel):
    """Schema for a list of learning sessions."""
    sessions: list[LearningSessionResponse]
    total: int


class LearningSessionCompleteResponse(BaseModel):
    """Schema for session completion response with integration flags."""
    id: int
    uuid: str
    journey_id: int
    title: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    activity_created: bool = False
    journey_updated: bool = False
    streak_updated: bool = False
    achievements_checked: bool = False
