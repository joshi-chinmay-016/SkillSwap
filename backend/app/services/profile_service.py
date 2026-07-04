from sqlalchemy.orm import Session

from app.models.profile import Profile

from app.repositories.profile_repository import (
    get_profile_by_user_id,
    create_profile,
    update_profile
)


def get_or_create_profile(
    db: Session,
    user_id: int
):

    profile = get_profile_by_user_id(
        db,
        user_id
    )

    if not profile:

        profile = Profile(
            user_id=user_id
        )

        profile = create_profile(
            db,
            profile
        )

    return profile


def update_user_profile(
    db: Session,
    user_id: int,
    bio: str | None,
    department: str | None,
    year: int | None,
    avatar_url: str | None
):

    profile = get_or_create_profile(
        db,
        user_id
    )

    profile.bio = bio
    profile.department = department
    profile.year = year
    profile.avatar_url = avatar_url

    return update_profile(
        db,
        profile
    )