from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.current_user import (
    get_current_user
)

from app.schemas.notification import (
    NotificationResponse
)

from app.services.notification_service import (
    list_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    get_unread_count
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@router.get("/unread/count")
def unread(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return {
        "count": get_unread_count(
            db,
            current_user.id
        )
    }


@router.get(
    "",
    response_model=list[
        NotificationResponse
    ]
)
def get_notifications(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return list_notifications(
        db,
        current_user.id
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse
)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db)
):

    return mark_notification_read(
        db,
        notification_id
    )



@router.patch("/read-all")
def mark_all_read(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    mark_all_notifications_read(
        db,
        current_user.id
    )

    return {"message": "All notifications marked as read"}