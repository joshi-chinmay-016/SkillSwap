from pydantic import BaseModel


class FeedbackCreate(BaseModel):

    session_id: int

    reviewee_id: int

    rating: int

    comment: str


class FeedbackResponse(BaseModel):

    id: int

    session_id: int

    reviewer_id: int

    reviewee_id: int

    rating: int

    comment: str

    class Config:
        from_attributes = True