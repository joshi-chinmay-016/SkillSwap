from sqlalchemy.orm import Session

from app.repositories.analytics_repository import (
    get_top_teach_skills,
    get_top_learn_skills
)

from app.repositories.analytics_repository import (
    get_mentor_metrics
)

def top_teach_skills(
    db: Session
):

    skills = get_top_teach_skills(
        db
    )

    return [
        {
            "skill_id": skill.id,
            "skill_name": skill.name,
            "count": skill.count
        }
        for skill in skills
    ]


def top_learn_skills(
    db: Session
):

    skills = get_top_learn_skills(
        db
    )

    return [
        {
            "skill_id": skill.id,
            "skill_name": skill.name,
            "count": skill.count
        }
        for skill in skills
    ]


def trending_skills(
    db: Session
):

    teach = top_teach_skills(
        db
    )

    learn = top_learn_skills(
        db
    )

    scores = {}

    for item in teach:

        scores[
            item["skill_name"]
        ] = item["count"]

    for item in learn:

        scores[
            item["skill_name"]
        ] = (
            scores.get(
                item["skill_name"],
                0
            )
            +
            item["count"]
        )

    result = []

    for skill_name, count in scores.items():

        result.append(
            {
                "skill_name": skill_name,
                "count": count
            }
        )

    result.sort(
        key=lambda x:
        x["count"],
        reverse=True
    )

    return result[:10]

def mentor_performance(
    db: Session,
    user_id: int
):

    metrics = get_mentor_metrics(
        db,
        user_id
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
        (metrics["average_rating"] * 20 * 0.40)
        +
        (completion_rate * 0.30)
        +
        (response_rate * 0.20)
        +
        (metrics["badges_count"] * 2 * 0.10)
    )

    return {
        "mentor_score": round(
            mentor_score,
            2
        ),

        "completion_rate": round(
            completion_rate,
            2
        ),

        "average_rating": round(
            metrics["average_rating"],
            2
        ),

        "response_rate": round(
            response_rate,
            2
        ),

        "completed_sessions":
        metrics["completed_sessions"],

        "cancelled_sessions":
        metrics["cancelled_sessions"],

        "accepted_requests":
        metrics["accepted_requests"],

        "received_requests":
        metrics["received_requests"]
    }