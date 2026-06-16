from sqlalchemy.orm import Session

from app.repositories.analytics_repository import (
    get_top_teach_skills,
    get_top_learn_skills
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

    return result