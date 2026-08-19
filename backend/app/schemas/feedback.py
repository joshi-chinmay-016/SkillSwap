from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)