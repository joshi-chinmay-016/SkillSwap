from pydantic import BaseModel


class MentorPerformanceResponse(
    BaseModel
):

    mentor_score: float

    completion_rate: float

    average_rating: float

    response_rate: float

    completed_sessions: int

    cancelled_sessions: int

    accepted_requests: int

    received_requests: int