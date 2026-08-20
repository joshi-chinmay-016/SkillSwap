from fastapi import (
    APIRouter,
    Depends,
    status
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
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
from app.core.rate_limiter import enforce_booking_rate_limit

router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"]
)


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_session(
    request: SessionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Enforce Redis-backed sliding-window rate limit
    enforce_booking_rate_limit(current_user.id)

    return schedule_session(
        db,
        requester_id=current_user.id,
        mentor_id=request.mentor_id,
        skill_id=request.skill_id,
        scheduled_at=request.scheduled_at,
        duration_minutes=request.duration_minutes,
        meeting_link=request.meeting_link
    )


@router.get(
    "/me",
    response_model=list[SessionResponse]
)
def get_my_sessions(
    current_user=Depends(get_current_user),
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
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return complete_session(
        db,
        session_id=session_id,
        current_user_id=current_user.id
    )


@router.patch(
    "/{session_id}/cancel",
    response_model=SessionResponse
)
def cancel(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return cancel_session(
        db,
        session_id=session_id,
        current_user_id=current_user.id
    )


@router.get(
    "/upcoming",
    response_model=list[SessionResponse]
)
def get_upcoming_sessions(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
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
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
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
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return cancelled_sessions_list(
        db,
        current_user.id
    )


@router.get(
    "/dashboard/counts"
)
def get_session_counts(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return session_dashboard(
        db,
        current_user.id
    )



