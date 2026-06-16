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
    get_user_name
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

            rating = get_average_rating(
                db,
                mentor_id
            )

            rating = float(
                rating or 0
            )

            completed_sessions = get_completed_sessions(
                db,
                mentor_id
            )

            feedback_count = get_feedback_count(
                db,
                mentor_id
            )

            mentor_name = get_user_name(
                db,
                mentor_id
            )

            score = (
                50
                +
                (rating / 5) * 25
                +
                min(
                    completed_sessions,
                    20
                ) * 0.75
                +
                min(
                    feedback_count,
                    20
                ) * 0.5
            )

            recommendations.append(
                {
                    "mentor_id": mentor_id,
                    "mentor_name": mentor_name,
                    "compatibility_score": round(
                        score,
                        2
                    ),
                    "average_rating": round(
                        rating,
                        2
                    ),
                    "completed_sessions": completed_sessions,
                    "feedback_count": feedback_count
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