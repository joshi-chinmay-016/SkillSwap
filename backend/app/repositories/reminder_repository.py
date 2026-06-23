from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.session import (
    Session as SessionModel
)


def get_upcoming_sessions(
    db: Session
):

    now = datetime.utcnow()

    next_24_hours = (
        now
        +
        timedelta(hours=24)
    )

    return (
        db.query(SessionModel)
        .filter(
            SessionModel.status == "scheduled",
            SessionModel.scheduled_at >= now,
            SessionModel.scheduled_at <= next_24_hours
        )
        .all()
    )