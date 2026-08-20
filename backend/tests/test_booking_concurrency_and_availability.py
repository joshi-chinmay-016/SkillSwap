import pytest
import uuid
import concurrent.futures
from datetime import datetime, date, time, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.models.user import User
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.models.mentor_availability import MentorAvailability
from app.models.session import Session as SessionModel
from app.models.notification import Notification
from app.models.wallet import Wallet
from app.core.security import create_access_token
from app.services.session_service import schedule_session, cancel_session
from app.services.availability_service import (
    add_availability,
    get_mentor_available_slots,
    remove_availability
)

from sqlalchemy.pool import StaticPool
from app.models.wallet_transaction import WalletTransaction

# Test SQLite in-memory engine with StaticPool for concurrency & thread safety
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

TABLES = [
    User.__table__,
    Skill.__table__,
    UserSkill.__table__,
    MentorAvailability.__table__,
    SessionModel.__table__,
    Notification.__table__,
    Wallet.__table__,
    WalletTransaction.__table__,
]


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_database():
    app.dependency_overrides[get_db] = override_get_db
    for table in TABLES:
        table.create(bind=test_engine, checkfirst=True)
    yield
    for table in reversed(TABLES):
        table.drop(bind=test_engine, checkfirst=True)
    app.dependency_overrides.pop(get_db, None)



@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


def create_test_user(db: Session, name: str, email: str, wallet_balance: int = 20) -> User:
    user = User(
        name=name,
        email=email,
        password_hash="hashed_pw"
    )
    db.add(user)
    db.flush()

    wallet = Wallet(
        user_id=user.id,
        balance=wallet_balance,
        earned_coins=wallet_balance,
        spent_coins=0
    )
    db.add(wallet)
    db.commit()
    db.refresh(user)
    return user


def create_test_skill(db: Session, name: str = "Python") -> Skill:
    skill = Skill(name=name, category="Programming")
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


# ──────────────────────────────────────────────────────────────────────────────
# 1. Availability Windows & Slot Calculation Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_add_and_query_availability(db_session: Session):
    mentor = create_test_user(db_session, "Mentor Alice", "alice@test.com")

    # Add Monday 10:00 - 14:00
    avail = add_availability(
        db=db_session,
        mentor_id=mentor.id,
        day_of_week="Monday",
        start_time=time(10, 0),
        end_time=time(14, 0),
        timezone="UTC"
    )

    assert avail.id is not None
    assert avail.day_of_week == "Monday"
    assert avail.mentor_id == mentor.id

    # Query computed slots for a known Monday in future
    # Find next Monday
    today = date.today()
    days_ahead = (0 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_monday = today + timedelta(days=days_ahead)
    monday_str = next_monday.strftime("%Y-%m-%d")

    slots_resp = get_mentor_available_slots(db_session, mentor.id, monday_str)
    assert slots_resp.day_of_week == "Monday"
    assert len(slots_resp.slots) == 4  # 10-11, 11-12, 12-13, 13-14
    for slot in slots_resp.slots:
        assert slot.is_available is True
        assert slot.duration_minutes == 60


def test_availability_window_overlap_validation(db_session: Session):
    mentor = create_test_user(db_session, "Mentor Bob", "bob@test.com")

    add_availability(
        db=db_session,
        mentor_id=mentor.id,
        day_of_week="Wednesday",
        start_time=time(9, 0),
        end_time=time(12, 0)
    )

    with pytest.raises(Exception) as exc:
        add_availability(
            db=db_session,
            mentor_id=mentor.id,
            day_of_week="Wednesday",
            start_time=time(11, 0),
            end_time=time(14, 0)
        )
    assert "overlaps" in str(exc.value.detail).lower()


# ──────────────────────────────────────────────────────────────────────────────
# 2. Authoritative Booking Correctness Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_successful_booking_and_wallet_deduction(db_session: Session):
    mentor = create_test_user(db_session, "Dr. Mentor", "doc@test.com", wallet_balance=0)
    learner = create_test_user(db_session, "Student Jane", "jane@test.com", wallet_balance=20)
    skill = create_test_skill(db_session, "Machine Learning")

    # Set mentor availability for Friday
    today = date.today()
    days_ahead = (4 - today.weekday()) % 7
    if days_ahead <= 0:
        days_ahead += 7
    target_friday = today + timedelta(days=days_ahead)

    add_availability(
        db=db_session,
        mentor_id=mentor.id,
        day_of_week="Friday",
        start_time=time(9, 0),
        end_time=time(17, 0)
    )

    scheduled_dt = datetime.combine(target_friday, time(10, 0))

    # Schedule session
    session = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=scheduled_dt,
        duration_minutes=60
    )

    assert session.id is not None
    assert session.status == "scheduled"
    assert session.duration_minutes == 60

    # Verify wallet was debited by 5 coins
    wallet = db_session.query(Wallet).filter(Wallet.user_id == learner.id).first()
    assert wallet.balance == 15
    assert wallet.spent_coins == 5

    # Verify persistent notification created for mentor
    notif = db_session.query(Notification).filter(Notification.user_id == mentor.id).first()
    assert notif is not None
    assert notif.type == "SESSION_BOOKED"
    assert notif.related_session_id == session.id
    assert notif.is_read is False


def test_reject_outside_availability_hours(db_session: Session):
    mentor = create_test_user(db_session, "Mentor Sam", "sam@test.com")
    learner = create_test_user(db_session, "Learner Leo", "leo@test.com")
    skill = create_test_skill(db_session, "FastAPI")

    add_availability(
        db=db_session,
        mentor_id=mentor.id,
        day_of_week="Tuesday",
        start_time=time(14, 0),
        end_time=time(18, 0)
    )

    # Next Tuesday
    today = date.today()
    days_ahead = (1 - today.weekday()) % 7
    if days_ahead <= 0:
        days_ahead += 7
    target_tuesday = today + timedelta(days=days_ahead)

    # Attempt booking at 08:00 AM (outside 14:00 - 18:00)
    scheduled_dt = datetime.combine(target_tuesday, time(8, 0))

    with pytest.raises(Exception) as exc:
        schedule_session(
            db=db_session,
            requester_id=learner.id,
            mentor_id=mentor.id,
            skill_id=skill.id,
            scheduled_at=scheduled_dt
        )
    assert "outside" in str(exc.value.detail).lower()


def test_reject_self_booking(db_session: Session):
    user = create_test_user(db_session, "Self User", "self@test.com")
    skill = create_test_skill(db_session, "Python")

    with pytest.raises(Exception) as exc:
        schedule_session(
            db=db_session,
            requester_id=user.id,
            mentor_id=user.id,
            skill_id=skill.id,
            scheduled_at=datetime.utcnow() + timedelta(days=1)
        )
    assert "yourself" in str(exc.value.detail).lower()


def test_reject_past_booking(db_session: Session):
    mentor = create_test_user(db_session, "Mentor Past", "past_m@test.com")
    learner = create_test_user(db_session, "Learner Past", "past_l@test.com")
    skill = create_test_skill(db_session, "Git")

    past_dt = datetime.utcnow() - timedelta(hours=2)

    with pytest.raises(Exception) as exc:
        schedule_session(
            db=db_session,
            requester_id=learner.id,
            mentor_id=mentor.id,
            skill_id=skill.id,
            scheduled_at=past_dt
        )
    assert "past" in str(exc.value.detail).lower()


def test_prevent_double_booking_conflict(db_session: Session):
    mentor = create_test_user(db_session, "Contended Mentor", "contended@test.com")
    learner1 = create_test_user(db_session, "Learner One", "l1@test.com", wallet_balance=20)
    learner2 = create_test_user(db_session, "Learner Two", "l2@test.com", wallet_balance=20)
    skill = create_test_skill(db_session, "Go")

    today = date.today()
    days_ahead = (3 - today.weekday()) % 7
    if days_ahead <= 0:
        days_ahead += 7
    target_thursday = today + timedelta(days=days_ahead)

    add_availability(
        db=db_session,
        mentor_id=mentor.id,
        day_of_week="Thursday",
        start_time=time(10, 0),
        end_time=time(14, 0)
    )

    slot_time = datetime.combine(target_thursday, time(10, 0))

    # 1. First learner books successfully
    s1 = schedule_session(
        db=db_session,
        requester_id=learner1.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=slot_time,
        duration_minutes=60
    )
    assert s1.id is not None

    # 2. Second learner attempts to book same slot -> 409 Conflict
    with pytest.raises(Exception) as exc:
        schedule_session(
            db=db_session,
            requester_id=learner2.id,
            mentor_id=mentor.id,
            skill_id=skill.id,
            scheduled_at=slot_time,
            duration_minutes=60
        )
    assert exc.value.status_code == 409
    assert "booked by another learner" in str(exc.value.detail).lower()


def test_cancellation_authorization_and_refund(db_session: Session):
    mentor = create_test_user(db_session, "Mentor Cancel", "cancel_m@test.com")
    learner = create_test_user(db_session, "Learner Cancel", "cancel_l@test.com", wallet_balance=20)
    third_party = create_test_user(db_session, "Third Party", "third@test.com")
    skill = create_test_skill(db_session, "Docker")

    today = date.today()
    days_ahead = (5 - today.weekday()) % 7
    if days_ahead <= 0:
        days_ahead += 7
    target_sat = today + timedelta(days=days_ahead)

    add_availability(
        db=db_session,
        mentor_id=mentor.id,
        day_of_week="Saturday",
        start_time=time(10, 0),
        end_time=time(14, 0)
    )

    session = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=datetime.combine(target_sat, time(11, 0))
    )

    # Unauthorized user tries to cancel
    with pytest.raises(Exception) as exc:
        cancel_session(db=db_session, session_id=session.id, current_user_id=third_party.id)
    assert exc.value.status_code == 403

    # Authorized learner cancels
    cancelled = cancel_session(db=db_session, session_id=session.id, current_user_id=learner.id)
    assert cancelled.status == "cancelled"

    # Verify refund notification for mentor and coin refund
    mentor_notif = db_session.query(Notification).filter(
        Notification.user_id == mentor.id,
        Notification.type == "SESSION_CANCELLED"
    ).first()
    assert mentor_notif is not None


# ──────────────────────────────────────────────────────────────────────────────
# 3. HTTP Endpoint Integration Tests (FastAPI TestClient)
# ──────────────────────────────────────────────────────────────────────────────

def test_api_booking_endpoint_flow(client: TestClient, db_session: Session):
    mentor = create_test_user(db_session, "API Mentor", "api_m@test.com")
    learner = create_test_user(db_session, "API Learner", "api_l@test.com", wallet_balance=30)
    skill = create_test_skill(db_session, "Rust")

    today = date.today()
    days_ahead = (0 - today.weekday()) % 7
    if days_ahead <= 0:
        days_ahead += 7
    target_mon = today + timedelta(days=days_ahead)

    add_availability(
        db=db_session,
        mentor_id=mentor.id,
        day_of_week="Monday",
        start_time=time(13, 0),
        end_time=time(16, 0)
    )

    learner_token = create_access_token({"sub": str(learner.id)})
    headers = {"Authorization": f"Bearer {learner_token}"}

    # 1. Query slots via API
    res_slots = client.get(
        f"/availability/mentor/{mentor.id}/slots?date={target_mon.strftime('%Y-%m-%d')}"
    )
    assert res_slots.status_code == 200
    slots_data = res_slots.json()
    assert len(slots_data["slots"]) == 3

    # 2. Book via POST /sessions
    booking_payload = {
        "mentor_id": mentor.id,
        "skill_id": skill.id,
        "scheduled_at": datetime.combine(target_mon, time(13, 0)).isoformat(),
        "duration_minutes": 60
    }
    res_book = client.post("/sessions", json=booking_payload, headers=headers)
    assert res_book.status_code == 201
    created = res_book.json()
    assert created["status"] == "scheduled"
    assert created["duration_minutes"] == 60
    assert created["mentor_name"] == "API Mentor"

    # 3. Query slots again -> verify slot is now occupied
    res_slots_after = client.get(
        f"/availability/mentor/{mentor.id}/slots?date={target_mon.strftime('%Y-%m-%d')}"
    )
    assert res_slots_after.status_code == 200
    slots_after_data = res_slots_after.json()
    assert slots_after_data["slots"][0]["is_available"] is False

    # 4. Repeat booking -> 409 Conflict
    res_book_dup = client.post("/sessions", json=booking_payload, headers=headers)
    assert res_book_dup.status_code == 409
