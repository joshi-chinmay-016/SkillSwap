from sqlalchemy.orm import Session
from app.models.mentor_availability import MentorAvailability


def create_availability(
    db: Session,
    availability: MentorAvailability
) -> MentorAvailability:
    db.add(availability)
    db.commit()
    db.refresh(availability)
    return availability


def get_my_availability(
    db: Session,
    mentor_id: int
) -> list[MentorAvailability]:
    return (
        db.query(MentorAvailability)
        .filter(
            MentorAvailability.mentor_id == mentor_id
        )
        .order_by(MentorAvailability.day_of_week, MentorAvailability.start_time)
        .all()
    )


def get_mentor_availabilities(
    db: Session,
    mentor_id: int,
    active_only: bool = True
) -> list[MentorAvailability]:
    query = db.query(MentorAvailability).filter(
        MentorAvailability.mentor_id == mentor_id
    )
    if active_only:
        query = query.filter(MentorAvailability.is_active.is_(True))
    return query.order_by(MentorAvailability.day_of_week, MentorAvailability.start_time).all()


def get_availability_for_day(
    db: Session,
    mentor_id: int,
    day_of_week: str,
    active_only: bool = True
) -> list[MentorAvailability]:
    query = db.query(MentorAvailability).filter(
        MentorAvailability.mentor_id == mentor_id,
        MentorAvailability.day_of_week.ilike(day_of_week)
    )
    if active_only:
        query = query.filter(MentorAvailability.is_active.is_(True))
    return query.all()


def get_availability_by_id(
    db: Session,
    availability_id: int
) -> MentorAvailability | None:
    return (
        db.query(MentorAvailability)
        .filter(MentorAvailability.id == availability_id)
        .first()
    )


def delete_availability(
    db: Session,
    availability_id: int
) -> bool:
    slot = get_availability_by_id(db, availability_id)
    if slot:
        db.delete(slot)
        db.commit()
        return True
    return False