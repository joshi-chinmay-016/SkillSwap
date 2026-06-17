from sqlalchemy.orm import Session

from app.models.mentor_availability import (
    MentorAvailability
)


def create_availability(
    db: Session,
    availability: MentorAvailability
):

    db.add(
        availability
    )

    db.commit()

    db.refresh(
        availability
    )

    return availability


def get_my_availability(
    db: Session,
    mentor_id: int
):

    return (
        db.query(
            MentorAvailability
        )
        .filter(
            MentorAvailability.mentor_id
            ==
            mentor_id
        )
        .all()
    )