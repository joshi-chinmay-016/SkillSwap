from pydantic import BaseModel


class DashboardResponse(BaseModel):

    completed_sessions: int

    scheduled_sessions: int

    cancelled_sessions: int

    average_rating: float

    feedback_count: int

    badges_count: int

    requests_sent: int

    requests_received: int

    skills_teaching: int

    skills_learning: int

    five_star_reviews: int

    four_star_reviews: int

    three_star_reviews: int