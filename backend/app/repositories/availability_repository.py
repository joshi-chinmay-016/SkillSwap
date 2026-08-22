from datetime import date
from typing import Optional
from sqlalchemy import or_, nullslast
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
        .order_by(
            nullslast(MentorAvailability.specific_date.asc()),
            MentorAvailability.day_of_week,
            MentorAvailability.start_time
        )
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
    return (
        query
        .order_by(
            nullslast(MentorAvailability.specific_date.asc()),
            MentorAvailability.day_of_week,
            MentorAvailability.start_time
        )
        .all()
    )


def get_availability_for_day(
    db: Session,
    mentor_id: int,
    day_of_week: str,
    active_only: bool = True
) -> list[MentorAvailability]:
    """Fetches recurring weekly availability windows for a given day of the week (where specific_date is NULL)."""
    query = db.query(MentorAvailability).filter(
        MentorAvailability.mentor_id == mentor_id,
        MentorAvailability.day_of_week.ilike(day_of_week),
        MentorAvailability.specific_date.is_(None)
    )
    if active_only:
        query = query.filter(MentorAvailability.is_active.is_(True))
    return query.all()


def get_availability_for_exact_date(
    db: Session,
    mentor_id: int,
    target_date: date,
    active_only: bool = True
) -> list[MentorAvailability]:
    """Fetches availability windows specifically registered for this exact calendar date."""
    query = db.query(MentorAvailability).filter(
        MentorAvailability.mentor_id == mentor_id,
        MentorAvailability.specific_date == target_date
    )
    if active_only:
        query = query.filter(MentorAvailability.is_active.is_(True))
    return query.all()


def get_availability_for_date_or_day(
    db: Session,
    mentor_id: int,
    target_date: date,
    day_of_week: str,
    active_only: bool = True
) -> list[MentorAvailability]:
    """
    Authoritative query: Returns active availability windows for a date.
    Matches:
    1) Specific date windows (specific_date == target_date)
    2) Recurring weekly windows for that day of week (day_of_week == day_of_week AND specific_date IS NULL)
    """
    query = db.query(MentorAvailability).filter(
        MentorAvailability.mentor_id == mentor_id,
        or_(
            MentorAvailability.specific_date == target_date,
            (
                MentorAvailability.day_of_week.ilike(day_of_week) &
                MentorAvailability.specific_date.is_(None)
            )
        )
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