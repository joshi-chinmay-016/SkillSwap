from sqlalchemy.orm import Session
from app.models.notification import Notification


def create_notification(
    db: Session,
    notification: Notification
) -> Notification:
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_notifications(
    db: Session,
    user_id: int,
    limit: int = 50
) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(limit)
        .all()
    )


def get_notification_by_id(
    db: Session,
    notification_id: int
) -> Notification | None:
    return (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )


def unread_count(
    db: Session,
    user_id: int
) -> int:
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.is_read.is_(False)
        )
        .count()
    )


def mark_all_read(
    db: Session,
    user_id: int
) -> None:
    (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.is_read.is_(False)
        )
        .update({"is_read": True})
    )
    db.commit()