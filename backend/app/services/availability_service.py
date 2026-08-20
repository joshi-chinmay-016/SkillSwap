import json
import logging
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.mentor_availability import MentorAvailability
from app.models.session import Session as SessionModel
from app.repositories.availability_repository import (
    create_availability,
    get_my_availability,
    get_mentor_availabilities,
    get_availability_for_day,
    get_availability_by_id,
    delete_availability
)
from app.schemas.availability import BookableSlot, MentorAvailabilitySlotsResponse
from app.core.redis import redis_client
from app.core.config import settings

logger = logging.getLogger("skillswap.availability")

VALID_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def invalidate_mentor_availability_cache(mentor_id: int) -> None:
    """Invalidates all Redis cache keys for a mentor's availability."""
    try:
        redis_client.delete_pattern(f"mentor_availability:{mentor_id}*")
    except Exception as e:
        logger.warning(f"Failed to invalidate availability cache for mentor {mentor_id}: {e}")


def add_availability(
    db: Session,
    mentor_id: int,
    day_of_week: str,
    start_time: time,
    end_time: time,
    timezone: str = "UTC",
    is_active: bool = True
) -> MentorAvailability:
    # Normalize day
    day_normalized = day_of_week.strip().capitalize()
    if day_normalized not in VALID_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid day of week '{day_of_week}'. Must be one of {VALID_DAYS}"
        )

    if start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time must be strictly earlier than end_time"
        )

    # Check for overlapping window for the same day
    existing_windows = get_availability_for_day(db, mentor_id, day_normalized, active_only=False)
    for w in existing_windows:
        if w.is_active and not (end_time <= w.start_time or start_time >= w.end_time):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Availability window overlaps with existing {day_normalized} window ({w.start_time.strftime('%H:%M')} - {w.end_time.strftime('%H:%M')})"
            )

    availability = MentorAvailability(
        mentor_id=mentor_id,
        day_of_week=day_normalized,
        start_time=start_time,
        end_time=end_time,
        timezone=timezone or "UTC",
        is_active=is_active
    )

    created = create_availability(db, availability)
    invalidate_mentor_availability_cache(mentor_id)
    return created


def my_availability(
    db: Session,
    mentor_id: int
) -> list[MentorAvailability]:
    return get_my_availability(db, mentor_id)


def mentor_availability_list(
    db: Session,
    mentor_id: int
) -> list[MentorAvailability]:
    cache_key = f"mentor_availability:{mentor_id}:windows"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            # We fetch from DB for ORM objects, or return cached summaries
            pass
    except Exception:
        pass

    results = get_mentor_availabilities(db, mentor_id, active_only=True)
    return results


def get_mentor_available_slots(
    db: Session,
    mentor_id: int,
    target_date_str: str
) -> MentorAvailabilitySlotsResponse:
    """
    Authoritative computation of bookable discrete 60-minute slots for a mentor on a specific date.
    Cross-references mentor availability windows against existing scheduled sessions in PostgreSQL.
    """
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Expected YYYY-MM-DD"
        )

    day_of_week = target_date.strftime("%A")
    cache_key = f"mentor_availability:{mentor_id}:slots:{target_date_str}"

    try:
        cached = redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            return MentorAvailabilitySlotsResponse(**data)
    except Exception:
        pass

    # 1. Fetch active availability windows for that day of week
    windows = get_availability_for_day(db, mentor_id, day_of_week, active_only=True)
    if not windows:
        response = MentorAvailabilitySlotsResponse(
            mentor_id=mentor_id,
            date=target_date_str,
            day_of_week=day_of_week,
            timezone="UTC",
            slots=[]
        )
        try:
            redis_client.setex(cache_key, 60, json.dumps(response.model_dump(mode="json")))
        except Exception:
            pass
        return response

    # 2. Fetch existing scheduled sessions for this mentor on target_date
    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)

    booked_sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.mentor_id == mentor_id,
            SessionModel.status == "scheduled",
            SessionModel.scheduled_at >= start_of_day,
            SessionModel.scheduled_at <= end_of_day
        )
        .all()
    )

    booked_intervals = []
    for s in booked_sessions:
        s_start = s.scheduled_at
        # Remove timezone offset if naive comparison needed
        if s_start.tzinfo is not None:
            s_start = s_start.replace(tzinfo=None)
        s_duration = getattr(s, "duration_minutes", 60) or 60
        s_end = s_start + timedelta(minutes=s_duration)
        booked_intervals.append((s_start, s_end))

    # 3. Generate candidate 60-minute slots
    slots = []
    now_utc = datetime.utcnow()
    primary_tz = windows[0].timezone if windows else "UTC"

    for window in windows:
        window_start_dt = datetime.combine(target_date, window.start_time)
        window_end_dt = datetime.combine(target_date, window.end_time)

        curr_start = window_start_dt
        while curr_start + timedelta(minutes=60) <= window_end_dt:
            curr_end = curr_start + timedelta(minutes=60)

            # Check if in past
            is_past = curr_start <= now_utc

            # Check conflict with booked sessions
            is_conflict = False
            for b_start, b_end in booked_intervals:
                if not (curr_end <= b_start or curr_start >= b_end):
                    is_conflict = True
                    break

            is_available = (not is_past) and (not is_conflict)

            fmt_time = f"{curr_start.strftime('%I:%M %p')} - {curr_end.strftime('%I:%M %p')}"

            slots.append(
                BookableSlot(
                    slot_start=curr_start,
                    slot_end=curr_end,
                    duration_minutes=60,
                    formatted_time=fmt_time,
                    is_available=is_available
                )
            )

            curr_start += timedelta(minutes=60)

    # Sort slots chronologically
    slots.sort(key=lambda s: s.slot_start)

    response = MentorAvailabilitySlotsResponse(
        mentor_id=mentor_id,
        date=target_date_str,
        day_of_week=day_of_week,
        timezone=primary_tz,
        slots=slots
    )

    try:
        redis_client.setex(cache_key, getattr(settings, "AVAILABILITY_CACHE_TTL_SECONDS", 120), json.dumps(response.model_dump(mode="json")))
    except Exception:
        pass

    return response


def remove_availability(
    db: Session,
    current_user_id: int,
    availability_id: int
) -> bool:
    slot = get_availability_by_id(db, availability_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability slot not found"
        )

    if slot.mentor_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own availability slots"
        )

    mentor_id = slot.mentor_id
    success = delete_availability(db, availability_id)
    if success:
        invalidate_mentor_availability_cache(mentor_id)
    return success