from sqlalchemy.orm import Session

from app.repositories.leaderboard_repository import (
    get_top_rated_users
)


def top_rated_users(
    db: Session
):

    results = get_top_rated_users(db)

    return [
        {
            "user_id": row.user_id,
            "average_rating": round(
                float(row.average_rating),
                2
            ),
            "total_reviews": row.total_reviews
        }
        for row in results
    ]