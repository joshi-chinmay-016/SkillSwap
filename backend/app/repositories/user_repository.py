from sqlalchemy.orm import Session

from app.models.user import User


import sqlalchemy as sa

def get_user_by_email(
    db: Session,
    email: str
):
    if not email:
        return None
    clean_email = email.strip().lower()
    return (
        db.query(User)
        .filter(sa.func.lower(User.email) == clean_email)
        .first()
    )


def get_user_by_id(
    db: Session,
    user_id: int
):
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )


def create_user(
    db: Session,
    user: User
):
    db.add(user)
    db.commit()
    db.refresh(user)

    return user