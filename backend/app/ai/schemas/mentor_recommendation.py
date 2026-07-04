from typing import List

from pydantic import (
    BaseModel,
    Field
)


class MentorRecommendationRequest(BaseModel):

    target_skill: str = Field(
        min_length=2
    )


class RecommendedMentor(BaseModel):

    mentor_name: str

    expertise: List[str]

    reason: str


class MentorRecommendationResponse(BaseModel):

    mentors: List[
        RecommendedMentor
    ]