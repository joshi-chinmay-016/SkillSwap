from sqlalchemy.orm import Session

from app.models.session import (
    Session as SessionModel
)

from app.repositories.session_repository import (
    create_session,
    get_sessions_by_user,
    get_session_by_id
)


def schedule_session(
    db: Session,
    requester_id: int,
    mentor_id: int,
    skill_id: int,
    scheduled_at,
    meeting_link
):

    session = SessionModel(
        requester_id=requester_id,
        mentor_id=mentor_id,
        skill_id=skill_id,
        scheduled_at=scheduled_at,
        meeting_link=meeting_link,
        status="scheduled"
    )

    return create_session(
        db,
        session
    )


def my_sessions(
    db: Session,
    user_id: int
):

    return get_sessions_by_user(
        db,
        user_id
    )


def complete_session(
    db: Session,
    session_id: int
):

    session = get_session_by_id(
        db,
        session_id
    )

    session.status = "completed"

    db.commit()

    db.refresh(session)

    return session


def cancel_session(
    db: Session,
    session_id: int
):

    session = get_session_by_id(
        db,
        session_id
    )

    session.status = "cancelled"

    db.commit()

    db.refresh(session)

    return session