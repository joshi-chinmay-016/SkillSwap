from sqlalchemy.orm import Session

from app.models.notification import (
    Notification
)


def create_notification(
    db: Session,
    notification: Notification
):

    db.add(notification)

    db.commit()

    db.refresh(notification)

    return notification


def get_notifications(
    db: Session,
    user_id: int
):

    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id
        )
        .all()
    )


def get_notification_by_id(
    db: Session,
    notification_id: int
):

    return (
        db.query(Notification)
        .filter(
            Notification.id == notification_id
        )
        .first()
    )


def unread_count(
    db: Session,
    user_id: int
):

    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
        .count()
    )