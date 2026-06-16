from pydantic import BaseModel


class MentorResponse(
    BaseModel
):

    mentor_id: int

    mentor_name: str

    average_rating: float

    completed_sessions: int