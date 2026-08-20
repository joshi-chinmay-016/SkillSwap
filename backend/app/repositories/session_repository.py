from sqlalchemy.orm import Session
from app.models.session import Session as SessionModel
from datetime import datetime, timedelta
from sqlalchemy import or_, and_


def create_session(
    db: Session,
    session: SessionModel
) -> SessionModel:
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_sessions_by_user(
    db: Session,
    user_id: int
) -> list[SessionModel]:
    return (
        db.query(SessionModel)
        .filter(
            or_(
                SessionModel.requester_id == user_id,
                SessionModel.mentor_id == user_id
            )
        )
        .order_by(SessionModel.scheduled_at.desc())
        .all()
    )


def get_session_by_id(
    db: Session,
    session_id: int
) -> SessionModel | None:
    return (
        db.query(SessionModel)
        .filter(SessionModel.id == session_id)
        .first()
    )


def get_mentor_session_at_time(
    db: Session,
    mentor_id: int,
    scheduled_at: datetime
) -> SessionModel | None:
    return (
        db.query(SessionModel)
        .filter(
            SessionModel.mentor_id == mentor_id,
            SessionModel.scheduled_at == scheduled_at,
            SessionModel.status == "scheduled"
        )
        .first()
    )


def find_conflicting_mentor_session(
    db: Session,
    mentor_id: int,
    start_time: datetime,
    duration_minutes: int = 60
) -> SessionModel | None:
    """
    Checks for any active scheduled session for this mentor that overlaps [start_time, start_time + duration_minutes).
    """
    end_time = start_time + timedelta(minutes=duration_minutes)
    # Check sessions where scheduled_at < end_time and (scheduled_at + duration) > start_time
    candidates = (
        db.query(SessionModel)
        .filter(
            SessionModel.mentor_id == mentor_id,
            SessionModel.status == "scheduled"
        )
        .all()
    )
    for s in candidates:
        s_start = s.scheduled_at
        if s_start.tzinfo is not None:
            s_start = s_start.replace(tzinfo=None)
        s_dur = getattr(s, "duration_minutes", 60) or 60
        s_end = s_start + timedelta(minutes=s_dur)

        naive_start = start_time.replace(tzinfo=None) if start_time.tzinfo is not None else start_time
        naive_end = end_time.replace(tzinfo=None) if end_time.tzinfo is not None else end_time

        if not (naive_end <= s_start or naive_start >= s_end):
            return s
    return None


def find_conflicting_requester_session(
    db: Session,
    requester_id: int,
    start_time: datetime,
    duration_minutes: int = 60
) -> SessionModel | None:
    """
    Checks for any active scheduled session for this requester (as learner or mentor) that overlaps [start_time, start_time + duration_minutes).
    """
    end_time = start_time + timedelta(minutes=duration_minutes)
    candidates = (
        db.query(SessionModel)
        .filter(
            or_(
                SessionModel.requester_id == requester_id,
                SessionModel.mentor_id == requester_id
            ),
            SessionModel.status == "scheduled"
        )
        .all()
    )
    for s in candidates:
        s_start = s.scheduled_at
        if s_start.tzinfo is not None:
            s_start = s_start.replace(tzinfo=None)
        s_dur = getattr(s, "duration_minutes", 60) or 60
        s_end = s_start + timedelta(minutes=s_dur)

        naive_start = start_time.replace(tzinfo=None) if start_time.tzinfo is not None else start_time
        naive_end = end_time.replace(tzinfo=None) if end_time.tzinfo is not None else end_time

        if not (naive_end <= s_start or naive_start >= s_end):
            return s
    return None


def get_sessions_by_status(
    db: Session,
    user_id: int,
    status: str
) -> list[SessionModel]:
    return (
        db.query(SessionModel)
        .filter(
            or_(
                SessionModel.requester_id == user_id,
                SessionModel.mentor_id == user_id
            ),
            SessionModel.status == status
        )
        .order_by(SessionModel.scheduled_at.desc())
        .all()
    )


def count_sessions_by_status(
    db: Session,
    user_id: int,
    status: str
) -> int:
    return (
        db.query(SessionModel)
        .filter(
            or_(
                SessionModel.requester_id == user_id,
                SessionModel.mentor_id == user_id
            ),
            SessionModel.status == status
        )
        .count()
    )


def get_upcoming_sessions_for_reminders(
    db: Session
) -> list[SessionModel]:
    now = datetime.utcnow()
    next_24_hours = now + timedelta(hours=24)

    return (
        db.query(SessionModel)
        .filter(
            SessionModel.status == "scheduled",
            SessionModel.scheduled_at >= now,
            SessionModel.scheduled_at <= next_24_hours
        )
        .all()
    )