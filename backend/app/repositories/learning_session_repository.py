import uuid as uuid_lib
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.learning_session import LearningSession
from typing import Optional, List


def create_session(
    db: Session,
    user_id: int,
    journey_id: int,
    title: str
) -> LearningSession:
    """Create a new learning session in the database."""
    session = LearningSession(
        uuid=str(uuid_lib.uuid4()),
        user_id=user_id,
        journey_id=journey_id,
        title=title,
        status="ACTIVE"
    )
    db.add(session)
    db.flush()
    return session


def get_session(
    db: Session,
    session_id: int
) -> Optional[LearningSession]:
    """Retrieve a learning session by its integer ID."""
    return (
        db.query(LearningSession)
        .filter(LearningSession.id == session_id)
        .first()
    )


def get_session_by_uuid(
    db: Session,
    uuid: str
) -> Optional[LearningSession]:
    """Retrieve a learning session by its UUID."""
    return (
        db.query(LearningSession)
        .filter(LearningSession.uuid == uuid)
        .first()
    )


def get_user_session(
    db: Session,
    session_id: int,
    user_id: int
) -> Optional[LearningSession]:
    """Retrieve a learning session scoped to a specific user."""
    return (
        db.query(LearningSession)
        .filter(
            LearningSession.id == session_id,
            LearningSession.user_id == user_id
        )
        .first()
    )


def get_journey_sessions(
    db: Session,
    journey_id: int
) -> List[LearningSession]:
    """Retrieve all learning sessions for a journey, ordered newest first."""
    return (
        db.query(LearningSession)
        .filter(LearningSession.journey_id == journey_id)
        .order_by(desc(LearningSession.created_at), desc(LearningSession.id))
        .all()
    )


def complete_session(
    db: Session,
    session: LearningSession
) -> LearningSession:
    """Mark a learning session as COMPLETED and set ended_at."""
    session.status = "COMPLETED"
    session.ended_at = datetime.now(timezone.utc)
    db.flush()
    return session


def archive_session(
    db: Session,
    session: LearningSession
) -> LearningSession:
    """Mark a learning session as ARCHIVED."""
    session.status = "ARCHIVED"
    db.flush()
    return session
