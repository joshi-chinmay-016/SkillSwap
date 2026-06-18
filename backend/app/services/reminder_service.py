from sqlalchemy.orm import Session

from app.repositories.session_repository import (
    get_upcoming_sessions_for_reminders
)

from app.services.notification_service import (
    create_user_notification
)


def send_session_reminders(
    db: Session
):

    sessions = (
        get_upcoming_sessions_for_reminders(
            db
        )
    )

    reminders_sent = 0

    for session in sessions:

        create_user_notification(
            db,
            session.requester_id,
            (
                f"Reminder: You have a session "
                f"scheduled at "
                f"{session.scheduled_at}"
            )
        )

        create_user_notification(
            db,
            session.mentor_id,
            (
                f"Reminder: You have a session "
                f"scheduled at "
                f"{session.scheduled_at}"
            )
        )

        reminders_sent += 1

    return {
        "sessions_checked": len(
            sessions
        ),
        "reminders_sent": reminders_sent
    }