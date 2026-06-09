from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import (
    get_user_by_email,
    create_user
)
from app.core.security import hash_password


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

    return create_user(
        db,
        user
    )