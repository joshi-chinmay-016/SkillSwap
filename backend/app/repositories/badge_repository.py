from sqlalchemy.orm import Session

from app.models.badge import Badge


def create_badge(
    db: Session,
    badge: Badge
):

    db.add(badge)

    db.commit()

    db.refresh(badge)

    return badge


def get_user_badges(
    db: Session,
    user_id: int
):

    return (
        db.query(Badge)
        .filter(
            Badge.user_id == user_id
        )
        .all()
    )