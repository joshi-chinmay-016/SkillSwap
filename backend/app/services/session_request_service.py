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

    return create_request(
        db,
        request
    )


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

    return request