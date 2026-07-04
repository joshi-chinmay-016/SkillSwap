from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.current_user import (
    get_current_user
)

from app.schemas.session import (
    SessionCreate,
    SessionResponse
)

from app.services.session_service import (
    schedule_session,
    my_sessions,
    complete_session,
    cancel_session,
    upcoming_sessions,
    completed_sessions_list,
    cancelled_sessions_list,
    session_dashboard
)


router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"]
)


@router.post(
    "",
    response_model=SessionResponse
)
def create_session(
    request: SessionCreate,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return schedule_session(
        db,
        current_user.id,
        request.mentor_id,
        request.skill_id,
        request.scheduled_at,
        request.meeting_link
    )


@router.get(
    "/me",
    response_model=list[
        SessionResponse
    ]
)
def get_my_sessions(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return my_sessions(
        db,
        current_user.id
    )


@router.patch(
    "/{session_id}/complete",
    response_model=SessionResponse
)
def complete(
    session_id: int,
    db: Session = Depends(get_db)
):

    return complete_session(
        db,
        session_id
    )


@router.patch(
    "/{session_id}/cancel",
    response_model=SessionResponse
)
def cancel(
    session_id: int,
    db: Session = Depends(get_db)
):

    return cancel_session(
        db,
        session_id
    )

@router.get(
    "/upcoming",
    response_model=list[SessionResponse]
)
def get_upcoming_sessions(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    )
):

    return upcoming_sessions(
        db,
        current_user.id
    )


@router.get(
    "/completed",
    response_model=list[SessionResponse]
)
def get_completed_sessions(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    )
):

    return completed_sessions_list(
        db,
        current_user.id
    )


@router.get(
    "/cancelled",
    response_model=list[SessionResponse]
)
def get_cancelled_sessions(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    )
):

    return cancelled_sessions_list(
        db,
        current_user.id
    )


