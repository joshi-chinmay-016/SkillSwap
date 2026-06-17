from sqlalchemy.orm import Session

from app.repositories.mentor_repository import (
    get_teaching_users,
    get_teaching_users_by_skill
)

from app.repositories.recommendation_repository import (
    get_average_rating,
    get_completed_sessions
)


def discover_mentors(
    db: Session,
    skill: str = None,
    min_rating: float = None,
    page: int = 1,
    size: int = 10
):

    if skill:

        mentors = (
            get_teaching_users_by_skill(
                db,
                skill
            )
        )

    else:

        mentors = (
            get_teaching_users(
                db
            )
        )

    results = []

    for mentor in mentors:

        rating = (
            get_average_rating(
                db,
                mentor.id
            )
        )

        rating = float(
            rating or 0
        )

        completed_sessions = (
            get_completed_sessions(
                db,
                mentor.id
            )
        )

        if (
            min_rating is not None
            and
            rating < min_rating
        ):
            continue

        results.append(
            {
                "mentor_id": mentor.id,
                "mentor_name": mentor.name,
                "average_rating": round(
                    rating,
                    2
                ),
                "completed_sessions": completed_sessions
            }
        )

    results.sort(
        key=lambda x: (
            x["average_rating"],
            x["completed_sessions"]
        ),
        reverse=True
    )

    start = (
        page - 1
    ) * size

    end = start + size

    return results[
        start:end
    ]