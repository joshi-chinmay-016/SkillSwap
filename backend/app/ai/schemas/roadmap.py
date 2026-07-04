from pydantic import BaseModel, Field
from typing import List


class RoadmapRequest(BaseModel):

    current_skills: List[str] = Field(
        min_length=1
    )

    target_role: str = Field(
        min_length=2,
        max_length=100
    )

    experience_level: str = Field(
        min_length=2,
        max_length=50
    )

    duration_months: int = Field(
        ge=1,
        le=24
    )


class RoadmapWeek(BaseModel):

    week: int

    topic: str

    goal: str


class RoadmapResponse(BaseModel):

    title: str

    weeks: List[RoadmapWeek]