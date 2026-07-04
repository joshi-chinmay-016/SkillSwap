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


def get_availability_for_day(
    db: Session,
    mentor_id: int,
    day_of_week: str
):

    return (
        db.query(
            MentorAvailability
        )
        .filter(
            MentorAvailability.mentor_id
            ==
            mentor_id,
            MentorAvailability.day_of_week
            ==
            day_of_week
        )
        .first()
    )