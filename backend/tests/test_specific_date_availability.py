import pytest
from datetime import datetime, date, time, timedelta
from app.core.database import SessionLocal
from app.models.user import User
from app.models.skill import Skill
from app.services.availability_service import (
    add_availability,
    get_mentor_available_slots,
    my_availability,
    remove_availability
)
from app.services.session_service import schedule_session
from app.services.wallet_service import credit_wallet


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_specific_date_availability_creation_and_slots(db_session):
    # 1. Setup mentor and learner
    import uuid
    uid = uuid.uuid4().hex[:8]
    mentor = User(name=f"Mentor {uid}", email=f"mentor_{uid}@example.com", password_hash="hash")
    learner = User(name=f"Learner {uid}", email=f"learner_{uid}@example.com", password_hash="hash")
    skill = Skill(name=f"Skill_{uid}", category="Tech")
    db_session.add_all([mentor, learner, skill])
    db_session.commit()
    db_session.refresh(mentor)
    db_session.refresh(learner)
    db_session.refresh(skill)

    credit_wallet(db_session, learner.id, 50, "Test funds")

    # 2. Add availability for a specific future date (e.g. 5 days from now)
    target_date = date.today() + timedelta(days=5)
    target_date_str = target_date.strftime("%Y-%m-%d")
    expected_weekday = target_date.strftime("%A")

    avail = add_availability(
        db=db_session,
        mentor_id=mentor.id,
        specific_date=target_date,
        start_time=time(10, 0),
        end_time=time(14, 0),
        timezone="UTC"
    )

    assert avail.id is not None
    assert avail.specific_date == target_date
    assert avail.day_of_week == expected_weekday

    # 3. Query slots for that specific date
    slots_resp = get_mentor_available_slots(db_session, mentor.id, target_date_str)
    assert slots_resp.mentor_id == mentor.id
    assert slots_resp.date == target_date_str
    assert slots_resp.day_of_week == expected_weekday
    assert len(slots_resp.slots) == 4  # 10-11, 11-12, 12-13, 13-14

    # 4. Book the first slot
    booking_time = datetime.combine(target_date, time(10, 0))
    session = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=booking_time,
        duration_minutes=60
    )

    assert session.id is not None
    assert session.status == "scheduled"

    # 5. Query slots again - 10:00 AM slot must now be unavailable
    slots_after_booking = get_mentor_available_slots(db_session, mentor.id, target_date_str)
    slot_10am = next(s for s in slots_after_booking.slots if s.formatted_time.startswith("10:00 AM"))
    assert slot_10am.is_available is False
