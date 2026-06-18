from sqlalchemy.orm import Session

from app.models.session import (
    Session as SessionModel
)

from app.repositories.session_repository import (
    create_session,
    get_sessions_by_user,
    get_session_by_id
)
from fastapi import HTTPException

from app.repositories.availability_repository import (
    get_availability_for_day
)

from app.repositories.session_repository import (
    get_mentor_session_at_time
)

from app.repositories.session_repository import (
    get_sessions_by_status,
    count_sessions_by_status
)

def schedule_session(
    db: Session,
    requester_id: int,
    mentor_id: int,
    skill_id: int,
    scheduled_at,
    meeting_link
):

    day_of_week = (
        scheduled_at.strftime(
            "%A"
        )
    )

    availability = (
        get_availability_for_day(
            db,
            mentor_id,
            day_of_week
        )
    )

    if not availability:

        raise HTTPException(
            status_code=400,
            detail="Mentor unavailable on this day"
        )

    session_time = (
        scheduled_at.time()
    )

    if (
        session_time
        <
        availability.start_time
        or
        session_time
        >
        availability.end_time
    ):

        raise HTTPException(
            status_code=400,
            detail="Outside mentor availability"
        )

    existing_session = (
        get_mentor_session_at_time(
            db,
            mentor_id,
            scheduled_at
        )
    )

    if existing_session:

        raise HTTPException(
            status_code=400,
            detail="Time slot already booked"
        )

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

def upcoming_sessions(
    db: Session,
    user_id: int
):

    return get_sessions_by_status(
        db,
        user_id,
        "scheduled"
    )


def completed_sessions_list(
    db: Session,
    user_id: int
):

    return get_sessions_by_status(
        db,
        user_id,
        "completed"
    )


def cancelled_sessions_list(
    db: Session,
    user_id: int
):

    return get_sessions_by_status(
        db,
        user_id,
        "cancelled"
    )


def session_dashboard(
    db: Session,
    user_id: int
):

    return {
        "upcoming_sessions":
        count_sessions_by_status(
            db,
            user_id,
            "scheduled"
        ),

        "completed_sessions":
        count_sessions_by_status(
            db,
            user_id,
            "completed"
        ),

        "cancelled_sessions":
        count_sessions_by_status(
            db,
            user_id,
            "cancelled"
        )
    }