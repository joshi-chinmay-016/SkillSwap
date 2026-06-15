from pydantic import BaseModel


class DashboardResponse(BaseModel):

    completed_sessions: int

    scheduled_sessions: int

    average_rating: float

    feedback_count: int

    badges_count: int