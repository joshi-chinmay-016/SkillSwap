from sqlalchemy.orm import Session

from app.models.profile import Profile


def get_profile_by_user_id(
    db: Session,
    user_id: int
):

    return (
        db.query(Profile)
        .filter(
            Profile.user_id == user_id
        )
        .first()
    )


def create_profile(
    db: Session,
    profile: Profile
):

    db.add(profile)

    db.commit()

    db.refresh(profile)

    return profile


def update_profile(
    db: Session,
    profile: Profile
):

    db.commit()

    db.refresh(profile)

    return profile