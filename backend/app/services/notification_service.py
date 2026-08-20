from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.repositories.notification_repository import (
    create_notification,
    get_notifications,
    get_notification_by_id,
    unread_count,
    mark_all_read
)


def create_user_notification(
    db: Session,
    user_id: int,
    message: str,
    title: str | None = None,
    type: str = "GENERAL",
    related_session_id: int | None = None
) -> Notification:
    notification = Notification(
        user_id=user_id,
        message=message,
        title=title,
        type=type,
        related_session_id=related_session_id
    )

    return create_notification(
        db,
        notification
    )


def list_notifications(
    db: Session,
    user_id: int,
    limit: int = 50
) -> list[Notification]:
    return get_notifications(
        db,
        user_id,
        limit=limit
    )


def mark_notification_read(
    db: Session,
    notification_id: int,
    user_id: int
) -> Notification | None:
    notification = get_notification_by_id(
        db,
        notification_id
    )

    if not notification:
        return None

    if notification.user_id != user_id:
        return None

    notification.is_read = True
    db.commit()
    db.refresh(notification)

    return notification



def get_unread_count(
    db: Session,
    user_id: int
) -> int:
    return unread_count(
        db,
        user_id
    )


def mark_all_notifications_read(
    db: Session,
    user_id: int
) -> None:
    mark_all_read(
        db,
        user_id
    )