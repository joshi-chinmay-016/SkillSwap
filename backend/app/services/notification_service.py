from sqlalchemy.orm import Session

from app.models.notification import (
    Notification
)

from app.repositories.notification_repository import (
    create_notification,
    get_notifications,
    get_notification_by_id,
    unread_count
)


def create_user_notification(
    db: Session,
    user_id: int,
    message: str
):

    notification = Notification(
        user_id=user_id,
        message=message
    )

    return create_notification(
        db,
        notification
    )


def list_notifications(
    db: Session,
    user_id: int
):

    return get_notifications(
        db,
        user_id
    )


def mark_notification_read(
    db: Session,
    notification_id: int
):

    notification = get_notification_by_id(
        db,
        notification_id
    )

    notification.is_read = True

    db.commit()

    db.refresh(notification)

    return notification


def get_unread_count(
    db: Session,
    user_id: int
):

    return unread_count(
        db,
        user_id
    )