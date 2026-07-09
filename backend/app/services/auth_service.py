from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import Profile

from app.repositories.user_repository import (
    get_user_by_email,
    create_user
)

from app.repositories.profile_repository import (
    create_profile
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)


def register_user(
    db: Session,
    name: str,
    email: str,
    password: str
):

    existing_user = get_user_by_email(
        db,
        email
    )

    if existing_user:
        raise ValueError(
            "Email already exists"
        )

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password)
    )

    user = create_user(
        db,
        user
    )

    # Generate avatar URL using DiceBear
    avatar_url = f"https://api.dicebear.com/7.x/adventurer/svg?seed={name.replace(' ', '')}"

    # Create profile with avatar
    profile = Profile(
        user_id=user.id,
        avatar_url=avatar_url
    )

    create_profile(
        db,
        profile
    )

    return user


def login_user(
    db: Session,
    email: str,
    password: str
):

    user = get_user_by_email(
        db,
        email
    )

    if not user:
        raise ValueError(
            "Invalid credentials"
        )

    if not verify_password(
        password,
        user.password_hash
    ):
        raise ValueError(
            "Invalid credentials"
        )

    token = create_access_token(
        {
            "sub": str(user.id)
        }
    )

    return token