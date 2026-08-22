from pydantic import BaseModel, Field
from typing import List, Optional


class RoadmapRequest(BaseModel):
    current_skills: List[str] = Field(default_factory=list)
    target_role: str = Field(min_length=2, max_length=100)
    experience_level: str = Field(min_length=2, max_length=50, default="Beginner")
    duration_months: int = Field(ge=1, le=24, default=3)


class RoadmapTask(BaseModel):
    title: str
    description: Optional[str] = None
    resources: List[str] = Field(default_factory=list)


class RoadmapWeek(BaseModel):
    week: int
    topic: str
    goal: str
    tasks: List[RoadmapTask] = Field(default_factory=list)


class RoadmapResponse(BaseModel):
    title: str
    weeks: List[RoadmapWeek]