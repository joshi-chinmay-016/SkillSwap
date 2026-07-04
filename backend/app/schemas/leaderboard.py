from pydantic import BaseModel


class LeaderboardUser(BaseModel):

    user_id: int

    average_rating: float

    total_reviews: int