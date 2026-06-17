from sqlalchemy.orm import Session

from app.models.mentor_availability import (
    MentorAvailability
)

from app.repositories.availability_repository import (
    create_availability,
    get_my_availability
)


def add_availability(
    db: Session,
    mentor_id: int,
    day_of_week: str,
    start_time,
    end_time
):

    availability = (
        MentorAvailability(
            mentor_id=mentor_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time
        )
    )

    return create_availability(
        db,
        availability
    )


def my_availability(
    db: Session,
    mentor_id: int
):

    return get_my_availability(
        db,
        mentor_id
    )