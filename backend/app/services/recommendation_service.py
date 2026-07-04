import json

from sqlalchemy.orm import Session

from app.core.redis import (
    redis_client
)

from app.models.user_skill import UserSkill

from app.repositories.recommendation_repository import (
    get_mentors_for_skill,
    get_average_rating,
    get_completed_sessions,
    get_feedback_count,
    get_user_name,
    has_availability
)

from app.repositories.analytics_repository import (
    get_mentor_metrics
)


def get_recommendations(
    db: Session,
    current_user_id: int
):

    cache_key = (
        f"recommendations:user:{current_user_id}"
    )

    cached_data = redis_client.get(
        cache_key
    )

    if cached_data:

        return json.loads(
            cached_data
        )

    learn_skills = (
        db.query(UserSkill)
        .filter(
            UserSkill.user_id == current_user_id,
            UserSkill.type == "learn"
        )
        .all()
    )

    recommendations = []

    added_mentors = set()

    for skill in learn_skills:

        mentors = get_mentors_for_skill(
            db,
            skill.skill_id
        )

        for mentor in mentors:

            mentor_id = mentor.user_id

            if mentor_id == current_user_id:
                continue

            if mentor_id in added_mentors:
                continue

            mentor_name = get_user_name(
                db,
                mentor_id
            )

            rating = get_average_rating(
                db,
                mentor_id
            )

            rating = float(
                rating or 0
            )

            completed_sessions = (
                get_completed_sessions(
                    db,
                    mentor_id
                )
            )

            feedback_count = (
                get_feedback_count(
                    db,
                    mentor_id
                )
            )

            metrics = get_mentor_metrics(
                db,
                mentor_id
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
                (
                    metrics["badges_count"]
                    * 2
                    * 0.10
                )
            )

            availability = (
                has_availability(
                    db,
                    mentor_id
                )
            )

            availability_bonus = (
                20
                if availability
                else 0
            )

            score = (
                mentor_score
                +
                availability_bonus
            )

            recommendations.append(
                {
                    "mentor_id": mentor_id,

                    "mentor_name": mentor_name,

                    "compatibility_score": round(
                        score,
                        2
                    ),

                    "mentor_score": round(
                        mentor_score,
                        2
                    ),

                    "availability": availability,

                    "average_rating": round(
                        average_rating,
                        2
                    ),

                    "completed_sessions":
                    completed_sessions,

                    "feedback_count":
                    feedback_count
                }
            )

            added_mentors.add(
                mentor_id
            )

    recommendations.sort(
        key=lambda x:
        x["compatibility_score"],
        reverse=True
    )

    redis_client.setex(
        cache_key,
        300,
        json.dumps(
            recommendations
        )
    )

    return recommendations