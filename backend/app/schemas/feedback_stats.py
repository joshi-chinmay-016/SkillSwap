from pydantic import BaseModel


class FeedbackStatsResponse(BaseModel):

    average_rating: float

    total_reviews: int

    five_star_reviews: int

    four_star_reviews: int

    three_star_reviews: int

    two_star_reviews: int

    one_star_reviews: int