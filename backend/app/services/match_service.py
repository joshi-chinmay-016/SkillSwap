from sqlalchemy.orm import Session

from app.repositories.match_repository import (
    get_teachers,
    get_learners
)

from app.repositories.skill_repository import (
    get_user_skills
)

from app.repositories.user_repository import (
    get_user_by_id
)

from app.repositories.profile_repository import (
    get_profile_by_user_id
)

from app.repositories.skill_repository import (
    get_skill_by_id
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
    db,
    user_id: int
):

    my_skills = get_user_skills(
        db,
        user_id
    )

    enriched_matches = []

    for skill in my_skills:

        if skill.type == "learn":

            candidates = get_teachers(
                db,
                skill.skill_id
            )

        else:

            candidates = get_learners(
                db,
                skill.skill_id
            )

        for candidate in candidates:

            if candidate.user_id == user_id:
                continue

            user = get_user_by_id(
                db,
                candidate.user_id
            )

            profile = get_profile_by_user_id(
                db,
                candidate.user_id
            )

            skill_obj = get_skill_by_id(
                db,
                candidate.skill_id
            )

            enriched_matches.append(
                {
                    "user_id": user.id,
                    "name": user.name,
                    "department":
                        profile.department
                        if profile else None,
                    "year":
                        profile.year
                        if profile else None,
                    "skill":
                        skill_obj.name,
                    "type":
                        candidate.type
                }
            )

    return enriched_matches