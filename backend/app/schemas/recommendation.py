from pydantic import BaseModel


class RecommendationResponse(BaseModel):

    mentor_id: int

    mentor_name: str

    compatibility_score: float

    average_rating: float

    completed_sessions: int

    feedback_count: int