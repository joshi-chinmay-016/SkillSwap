from pydantic import BaseModel, ConfigDict


class RecommendationResponse(BaseModel):
    mentor_id: int
    mentor_name: str
    avatar_url: str | None = None
    department: str | None = None
    year: int | None = None

    compatibility_score: float
    mentor_score: float = 0.0
    availability: bool = False
    average_rating: float = 0.0
    completed_sessions: int = 0
    feedback_count: int = 0

    verification_status: str = "CLAIMED"
    credibility_score: float = 0.0

    matched_skills: list[str] = []
    reasons: list[str] = []

    model_config = ConfigDict(from_attributes=True)