from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.session import Session as SessionModel

ACTIVE_STATUSES = ["scheduled", "in_progress", "accepted"]


def _to_utc_naive(dt: datetime) -> datetime:
    """Standardizes datetime to UTC naive for comparison."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


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
    naive_dt = _to_utc_naive(scheduled_at)
    return (
        db.query(SessionModel)
        .filter(
            SessionModel.mentor_id == mentor_id,
            SessionModel.scheduled_at == naive_dt,
            SessionModel.status.in_(ACTIVE_STATUSES)
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
    Checks for any active/scheduled session for this mentor that overlaps [start_time, start_time + duration_minutes).
    """
    naive_start = _to_utc_naive(start_time)
    naive_end = naive_start + timedelta(minutes=duration_minutes)

    candidates = (
        db.query(SessionModel)
        .filter(
            SessionModel.mentor_id == mentor_id,
            SessionModel.status.in_(ACTIVE_STATUSES)
        )
        .all()
    )
    for s in candidates:
        s_start = _to_utc_naive(s.scheduled_at)
        s_dur = getattr(s, "duration_minutes", 60) or 60
        s_end = s_start + timedelta(minutes=s_dur)

        # Two intervals [A, B) and [C, D) overlap if A < D and C < B
        if naive_start < s_end and s_start < naive_end:
            return s
    return None


def find_conflicting_requester_session(
    db: Session,
    requester_id: int,
    start_time: datetime,
    duration_minutes: int = 60
) -> SessionModel | None:
    """
    Checks for any active/scheduled session for this requester (as learner or mentor) that overlaps [start_time, start_time + duration_minutes).
    """
    naive_start = _to_utc_naive(start_time)
    naive_end = naive_start + timedelta(minutes=duration_minutes)

    candidates = (
        db.query(SessionModel)
        .filter(
            or_(
                SessionModel.requester_id == requester_id,
                SessionModel.mentor_id == requester_id
            ),
            SessionModel.status.in_(ACTIVE_STATUSES)
        )
        .all()
    )
    for s in candidates:
        s_start = _to_utc_naive(s.scheduled_at)
        s_dur = getattr(s, "duration_minutes", 60) or 60
        s_end = s_start + timedelta(minutes=s_dur)

        if naive_start < s_end and s_start < naive_end:
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
    now = datetime.now(timezone.utc).replace(tzinfo=None)
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