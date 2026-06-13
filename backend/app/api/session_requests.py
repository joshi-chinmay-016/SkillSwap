from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.current_user import (
    get_current_user
)

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

router = APIRouter(
    prefix="/requests",
    tags=["Session Requests"]
)


@router.post(
    "",
    response_model=SessionRequestResponse
)
def create_session_request(
    request: SessionRequestCreate,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return send_request(
        db,
        current_user.id,
        request.receiver_id,
        request.skill_id
    )


@router.get(
    "/sent",
    response_model=list[
        SessionRequestResponse
    ]
)
def get_sent(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return sent_requests(
        db,
        current_user.id
    )


@router.get(
    "/received",
    response_model=list[
        SessionRequestResponse
    ]
)
def get_received(
    current_user=Depends(
        get_current_user
    ),
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
    db: Session = Depends(get_db)
):

    return accept_request(
        db,
        request_id
    )


@router.patch(
    "/{request_id}/reject",
    response_model=SessionRequestResponse
)
def reject(
    request_id: int,
    db: Session = Depends(get_db)
):

    return reject_request(
        db,
        request_id
    )