from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    Header,
    Response,
    status
)
from fastapi.responses import JSONResponse
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
    complete_session as complete_peer_session,
    cancel_session as cancel_peer_session,
    upcoming_sessions,
    completed_sessions_list,
    cancelled_sessions_list,
    session_dashboard,
    get_session_by_id_authorized
)
from app.repositories.session_repository import get_session_by_id as get_peer_session_by_id
from app.core.rate_limiter import enforce_booking_rate_limit, enforce_action_rate_limit
from app.core.idempotency import get_idempotent_response, save_idempotent_response

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
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    # 1. Check Idempotency Cache
    cached = get_idempotent_response(current_user.id, idempotency_key)
    if cached:
        cached_status, cached_data = cached
        return JSONResponse(status_code=cached_status, content=cached_data)

    # 2. Enforce Redis-backed sliding-window rate limit
    enforce_booking_rate_limit(current_user.id)

    # 3. Execute authoritative booking
    created_session = schedule_session(
        db,
        requester_id=current_user.id,
        mentor_id=request.mentor_id,
        skill_id=request.skill_id,
        scheduled_at=request.scheduled_at,
        duration_minutes=request.duration_minutes,
        meeting_link=request.meeting_link
    )

    # 4. Save result in idempotency cache
    response_obj = SessionResponse.model_validate(created_session)
    save_idempotent_response(
        user_id=current_user.id,
        key=idempotency_key,
        status_code=status.HTTP_201_CREATED,
        data=response_obj
    )

    return response_obj


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


@router.get(
    "/{session_id}",
    response_model=None
)
def get_session_detail(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if this ID belongs to a Peer Mentoring Session
    peer_session = get_peer_session_by_id(db, session_id)
    if peer_session:
        return get_session_by_id_authorized(
            db,
            session_id=session_id,
            current_user_id=current_user.id
        )

    # Otherwise forward to Learning Session service
    from app.services import learning_session_service
    return learning_session_service.get_session(
        db,
        session_id=session_id,
        user_id=current_user.id
    )


@router.patch(
    "/{session_id}/complete",
    response_model=None
)
def complete(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enforce_action_rate_limit("complete_session", current_user.id, limit=20, window_seconds=60)
    peer_session = get_peer_session_by_id(db, session_id)
    if peer_session:
        return complete_peer_session(
            db,
            session_id=session_id,
            current_user_id=current_user.id
        )

    from app.services import learning_session_service
    return learning_session_service.complete_session(
        db,
        session_id=session_id,
        user_id=current_user.id
    )


@router.patch(
    "/{session_id}/cancel",
    response_model=None
)
def cancel(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enforce_action_rate_limit("cancel_session", current_user.id, limit=20, window_seconds=60)
    peer_session = get_peer_session_by_id(db, session_id)
    if peer_session:
        return cancel_peer_session(
            db,
            session_id=session_id,
            current_user_id=current_user.id
        )

    from app.services import learning_session_service
    return learning_session_service.cancel_session(
        db,
        session_id=session_id,
        user_id=current_user.id
    )
