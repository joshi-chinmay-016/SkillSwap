from sqlalchemy.orm import Session

from app.repositories.leaderboard_repository import (
    get_top_rated_users
)

from app.repositories.leaderboard_repository import (
    get_most_active_mentors
)

from app.repositories.leaderboard_repository import (
    get_all_mentors
)

from app.repositories.analytics_repository import (
    get_mentor_metrics
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


def most_active_mentors(
    db: Session
):

    results = (
        get_most_active_mentors(
            db
        )
    )

    return [
        {
            "user_id": row.user_id,
            "completed_sessions":
            row.completed_sessions
        }
        for row in results
    ]


def top_mentors(
    db: Session
):

    mentors = (
        get_all_mentors(
            db
        )
    )

    leaderboard = []

    for mentor in mentors:

        metrics = (
            get_mentor_metrics(
                db,
                mentor.id
            )
        )

        average_rating = float(
            metrics["average_rating"] or 0
        )

        total_sessions = (
            metrics["completed_sessions"]
            +
            metrics["cancelled_sessions"]
        )

        completion_rate = (
            metrics["completed_sessions"]
            /
            total_sessions
            *
            100
            if total_sessions > 0
            else 0
        )

        response_rate = (
            metrics["accepted_requests"]
            /
            metrics["received_requests"]
            *
            100
            if metrics["received_requests"] > 0
            else 0
        )

        mentor_score = (
            (average_rating * 20 * 0.40)
            +
            (completion_rate * 0.30)
            +
            (response_rate * 0.20)
            +
            (metrics["badges_count"] * 2 * 0.10)
        )

        leaderboard.append(
            {
                "user_id": mentor.id,

                "mentor_score":
                round(
                    mentor_score,
                    2
                ),

                "average_rating":
                round(
                    average_rating,
                    2
                ),

                "completed_sessions":
                metrics[
                    "completed_sessions"
                ]
            }
        )

    leaderboard.sort(
        key=lambda x:
        x["mentor_score"],
        reverse=True
    )

    return leaderboard[:10]