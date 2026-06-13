from sqlalchemy.orm import Session

from app.models.session import Session as SessionModel


def create_session(
    db: Session,
    session: SessionModel
):

    db.add(session)

    db.commit()

    db.refresh(session)

    return session


def get_sessions_by_user(
    db: Session,
    user_id: int
):

    return (
        db.query(SessionModel)
        .filter(
            (SessionModel.requester_id == user_id)
            |
            (SessionModel.mentor_id == user_id)
        )
        .all()
    )


def get_session_by_id(
    db: Session,
    session_id: int
):

    return (
        db.query(SessionModel)
        .filter(
            SessionModel.id == session_id
        )
        .first()
    )