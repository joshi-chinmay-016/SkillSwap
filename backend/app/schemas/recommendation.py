from pydantic import BaseModel


class RecommendationResponse(BaseModel):

    mentor_id: int

    compatibility_score: float

    average_rating: float

    completed_sessions: int