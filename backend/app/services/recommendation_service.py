from sqlalchemy.orm import Session

from app.repositories.recommendation_repository import (
    get_mentors_for_skill,
    get_average_rating,
    get_completed_sessions
)

from app.models.user_skill import UserSkill


def get_recommendations(
    db: Session,
    current_user_id: int
):

    learn_skills = (
        db.query(UserSkill)
        .filter(
            UserSkill.user_id == current_user_id,
            UserSkill.type == "learn"
        )
        .all()
    )

    recommendations = []

    for skill in learn_skills:

        mentors = get_mentors_for_skill(
            db,
            skill.skill_id
        )

        for mentor in mentors:

            mentor_id = mentor.user_id

            if mentor_id == current_user_id:
                continue

            rating = get_average_rating(
                db,
                mentor_id
            )

            completed_sessions = get_completed_sessions(
                db,
                mentor_id
            )

            score = (
                50
                +
                (rating / 5) * 30
                +
                min(
                    completed_sessions,
                    20
                ) * 1
            )

            recommendations.append(
                {
                    "mentor_id": mentor_id,
                    "compatibility_score": round(
                        score,
                        2
                    ),
                    "average_rating": round(
                        float(rating),
                        2
                    ),
                    "completed_sessions": completed_sessions
                }
            )

    recommendations.sort(
        key=lambda x:
        x["compatibility_score"],
        reverse=True
    )

    return recommendations