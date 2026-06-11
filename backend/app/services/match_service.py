from sqlalchemy.orm import Session

from app.repositories.match_repository import (
    get_teachers,
    get_learners
)

from app.repositories.skill_repository import (
    get_user_skills
)


def find_teachers(
    db: Session,
    skill_id: int
):

    return get_teachers(
        db,
        skill_id
    )


def find_learners(
    db: Session,
    skill_id: int
):

    return get_learners(
        db,
        skill_id
    )


def get_my_matches(
    db: Session,
    user_id: int
):

    my_skills = get_user_skills(
        db,
        user_id
    )

    matches = []

    for skill in my_skills:

        if skill.type == "learn":

            teachers = get_teachers(
                db,
                skill.skill_id
            )

            matches.extend(
                teachers
            )

        elif skill.type == "teach":

            learners = get_learners(
                db,
                skill.skill_id
            )

            matches.extend(
                learners
            )

    return matches