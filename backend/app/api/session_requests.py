from fastapi import (
    APIRouter,
    Depends,
    status
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.schemas.session_request import (
    SessionRequestCreate,
    SessionRequestResponse
)
from app.services.session_request_service import (
    send_request,
    sent_requests,
    received_requests,
    accept_request,
    reject_request
)
from app.core.rate_limiter import enforce_action_rate_limit

router = APIRouter(
    prefix="/requests",
    tags=["Session Requests"]
)


@router.post(
    "",
    response_model=SessionRequestResponse,
    status_code=status.HTTP_201_CREATED
)
def create_session_request(
    request: SessionRequestCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enforce_action_rate_limit("create_request", current_user.id, limit=15, window_seconds=60)
    return send_request(
        db,
        current_user.id,
        request.receiver_id,
        request.skill_id
    )


@router.get(
    "/sent",
    response_model=list[SessionRequestResponse]
)
def get_sent(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return sent_requests(
        db,
        current_user.id
    )


@router.get(
    "/received",
    response_model=list[SessionRequestResponse]
)
def get_received(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return received_requests(
        db,
        current_user.id
    )


@router.patch(
    "/{request_id}/accept",
    response_model=SessionRequestResponse
)
def accept(
    request_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enforce_action_rate_limit("accept_request", current_user.id, limit=20, window_seconds=60)
    return accept_request(
        db,
        request_id,
        current_user.id
    )


@router.patch(
    "/{request_id}/reject",
    response_model=SessionRequestResponse
)
def reject(
    request_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enforce_action_rate_limit("reject_request", current_user.id, limit=20, window_seconds=60)
    return reject_request(
        db,
        request_id,
        current_user.id
    )