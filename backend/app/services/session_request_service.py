from sqlalchemy.orm import Session

from app.models.session_request import (
    SessionRequest
)

from app.repositories.session_request_repository import (
    create_request,
    get_sent_requests,
    get_received_requests,
    get_request_by_id
)

from app.services.notification_service import (
    create_user_notification
)


def send_request(
    db: Session,
    sender_id: int,
    receiver_id: int,
    skill_id: int
):

    request = SessionRequest(
        sender_id=sender_id,
        receiver_id=receiver_id,
        skill_id=skill_id,
        status="pending"
    )

    request = create_request(
        db,
        request
    )

    create_user_notification(
        db,
        receiver_id,
        f"You received a skill request from User {sender_id}"
    )

    return request


def sent_requests(
    db: Session,
    user_id: int
):

    return get_sent_requests(
        db,
        user_id
    )


def received_requests(
    db: Session,
    user_id: int
):

    return get_received_requests(
        db,
        user_id
    )


def accept_request(
    db: Session,
    request_id: int
):

    request = get_request_by_id(
        db,
        request_id
    )

    request.status = "accepted"

    db.commit()

    db.refresh(request)

    create_user_notification(
        db,
        request.sender_id,
        "Your request has been accepted"
    )

    return request


def reject_request(
    db: Session,
    request_id: int
):

    request = get_request_by_id(
        db,
        request_id
    )

    request.status = "rejected"

    db.commit()

    db.refresh(request)

    create_user_notification(
        db,
        request.sender_id,
        "Your request has been rejected"
    )

    return request