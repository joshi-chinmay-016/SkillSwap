from sqlalchemy.orm import Session

from app.models.session_request import (
    SessionRequest
)


def create_request(
    db: Session,
    request: SessionRequest
):

    db.add(request)

    db.commit()

    db.refresh(request)

    return request


def get_sent_requests(
    db: Session,
    user_id: int
):

    return (
        db.query(SessionRequest)
        .filter(
            SessionRequest.sender_id == user_id
        )
        .all()
    )


def get_received_requests(
    db: Session,
    user_id: int
):

    return (
        db.query(SessionRequest)
        .filter(
            SessionRequest.receiver_id == user_id
        )
        .all()
    )


def get_request_by_id(
    db: Session,
    request_id: int
):

    return (
        db.query(SessionRequest)
        .filter(
            SessionRequest.id == request_id
        )
        .first()
    )