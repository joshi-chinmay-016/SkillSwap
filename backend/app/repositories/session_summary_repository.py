import uuid as uuid_lib
from typing import Optional

from sqlalchemy.orm import Session

from app.models.session_summary import SessionSummary
from app.schemas.session_summary import SessionSummaryCreate, SessionSummaryUpdate


def create_summary(
    db: Session,
    session_id: int,
    data: SessionSummaryCreate
) -> SessionSummary:
    """
    Persist a new SessionSummary to the database.

    Responsibilities:
    - Assign a fresh UUID
    - Store all structured fields
    - Flush (do not commit — caller owns the transaction)
    """
    summary = SessionSummary(
        uuid=str(uuid_lib.uuid4()),
        session_id=session_id,
        summary=data.summary,
        key_takeaways=data.key_takeaways,
        strengths=data.strengths,
        weaknesses=data.weaknesses,
        follow_up_topics=data.follow_up_topics,
    )
    db.add(summary)
    db.flush()
    return summary


def get_summary(
    db: Session,
    summary_id: int
) -> Optional[SessionSummary]:
    """Retrieve a SessionSummary by its integer primary key."""
    return (
        db.query(SessionSummary)
        .filter(SessionSummary.id == summary_id)
        .first()
    )


def get_session_summary(
    db: Session,
    session_id: int
) -> Optional[SessionSummary]:
    """Retrieve the SessionSummary for a given LearningSession ID."""
    return (
        db.query(SessionSummary)
        .filter(SessionSummary.session_id == session_id)
        .first()
    )


def update_summary(
    db: Session,
    summary: SessionSummary,
    data: SessionSummaryUpdate
) -> SessionSummary:
    """
    Apply partial updates to an existing SessionSummary.

    Only fields provided (non-None) in `data` are updated.
    """
    update_fields = data.model_dump(exclude_none=True)
    for field, value in update_fields.items():
        setattr(summary, field, value)
    db.flush()
    return summary


def delete_summary(
    db: Session,
    summary: SessionSummary
) -> None:
    """Delete a SessionSummary from the database."""
    db.delete(summary)
    db.flush()
