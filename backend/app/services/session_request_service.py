import asyncio
import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.session_request import SessionRequest
from app.models.user import User
from app.models.skill import Skill
from app.repositories.session_request_repository import (
    create_request,
    get_sent_requests,
    get_received_requests,
    get_request_by_id
)
from app.services.notification_service import create_user_notification
from app.core.websocket_manager import manager
from app.core.logging import log_structured_event

logger = logging.getLogger("skillswap.session_requests")


def send_request(
    db: Session,
    sender_id: int,
    receiver_id: int,
    skill_id: int
) -> SessionRequest:
    if sender_id == receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot send a session request to yourself."
        )

    sender = db.query(User).filter(User.id == sender_id).first()
    receiver = db.query(User).filter(User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient user not found."
        )

    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found."
        )

    request = SessionRequest(
        sender_id=sender_id,
        receiver_id=receiver_id,
        skill_id=skill_id,
        status="pending"
    )

    request = create_request(db, request)

    sender_name = sender.name if sender else f"User #{sender_id}"
    create_user_notification(
        db,
        receiver_id,
        f"You received a {skill.name} session request from {sender_name}",
        title="New Session Request 📌",
        type="REQUEST_RECEIVED"
    )

    log_structured_event(
        "session_request_created",
        request_id=request.id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        skill_id=skill_id
    )

    # Real-time WebSocket dispatch
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            manager.send_notification_payload(
                receiver_id,
                {
                    "type": "REQUEST_RECEIVED",
                    "request_id": request.id,
                    "sender_id": sender_id,
                    "sender_name": sender_name,
                    "skill_name": skill.name,
                    "message": f"New session request from {sender_name}"
                }
            )
        )
    except RuntimeError:
        pass
    except Exception:
        pass

    return request


def sent_requests(
    db: Session,
    user_id: int
) -> list[SessionRequest]:
    return get_sent_requests(db, user_id)


def received_requests(
    db: Session,
    user_id: int
) -> list[SessionRequest]:
    return get_received_requests(db, user_id)


def accept_request(
    db: Session,
    request_id: int,
    current_user_id: int
) -> SessionRequest:
    request = get_request_by_id(db, request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session request not found."
        )

    # Authorization: Only the receiver (mentor) can accept
    if request.receiver_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to accept this request."
        )

    # State machine check
    if request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot accept a request that is already {request.status}."
        )

    request.status = "accepted"
    db.commit()
    db.refresh(request)

    create_user_notification(
        db,
        request.sender_id,
        "Your session request has been accepted! You can now coordinate or schedule a time.",
        title="Request Accepted ✅",
        type="REQUEST_ACCEPTED"
    )

    log_structured_event(
        "session_request_accepted",
        request_id=request.id,
        sender_id=request.sender_id,
        receiver_id=request.receiver_id
    )

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            manager.send_notification_payload(
                request.sender_id,
                {
                    "type": "REQUEST_ACCEPTED",
                    "request_id": request.id,
                    "message": "Your session request has been accepted."
                }
            )
        )
    except RuntimeError:
        pass
    except Exception:
        pass

    return request


def reject_request(
    db: Session,
    request_id: int,
    current_user_id: int
) -> SessionRequest:
    request = get_request_by_id(db, request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session request not found."
        )

    # Authorization: Only receiver can reject
    if request.receiver_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to reject this request."
        )

    if request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject a request that is already {request.status}."
        )

    request.status = "rejected"
    db.commit()
    db.refresh(request)

    create_user_notification(
        db,
        request.sender_id,
        "Your session request was declined by the mentor.",
        title="Request Declined",
        type="REQUEST_REJECTED"
    )

    log_structured_event(
        "session_request_rejected",
        request_id=request.id,
        sender_id=request.sender_id,
        receiver_id=request.receiver_id
    )

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            manager.send_notification_payload(
                request.sender_id,
                {
                    "type": "REQUEST_REJECTED",
                    "request_id": request.id,
                    "message": "Your session request has been rejected."
                }
            )
        )
    except RuntimeError:
        pass
    except Exception:
        pass

    return request