from typing import List

from pydantic import (
    BaseModel,
    Field
)


class SkillGapRequest(BaseModel):

    current_skills: List[str] = Field(
        min_length=1
    )

    target_role: str = Field(
        min_length=2,
        max_length=100
    )


class SkillGapResponse(BaseModel):

    target_role: str

    matched_skills: List[str]

    missing_skills: List[str]

    recommendations: List[str]