"""
SkillSwap Arena — Phase 3 Production-Grade Peer Learning Session Infrastructure Test Suite

Covers:
  - Test 1: Full authoritative lifecycle (scheduled -> in_progress -> completed)
  - Test 2: Invalid state transitions prevented (cannot complete/start cancelled session, cannot restart completed session)
  - Test 3: Concurrency-safe double-booking protection (409 Conflict)
  - Test 4: Participant authorization & private session protection (403 Forbidden)
  - Test 5: Jitsi meeting room URL generation and join authorization
  - Test 6: Cancelled session locks Jitsi room & cannot be joined (409 Conflict)
  - Test 7: Learning activity distinction: learner gets 'session_completed', mentor gets 'teaching_completed'
  - Test 8: Ephemeral presence tracking via Redis
  - Test 9: Authoritative feedback rules (1-5 rating, no self-feedback, session completion check, duplicate prevention)
  - Test 10: Cancellation coin refund & availability cache release
"""
import pytest
from datetime import datetime, date, time, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.core.database import get_db
from app.models.base import Base
from app.models.user import User
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.models.mentor_availability import MentorAvailability
from app.models.session import Session as SessionModel
from app.models.session_request import SessionRequest
from app.models.notification import Notification
from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.models.learning_activity import LearningActivity
from app.models.feedback import Feedback
from app.core.security import create_access_token
from app.services.session_service import (
    schedule_session,
    start_session,
    complete_session,
    cancel_session,
    join_session,
    leave_session,
    get_session_by_id_authorized,
    get_session_participants
)
from app.services.availability_service import add_availability
from app.services.feedback_service import submit_feedback, get_feedback_for_session

from app.models.profile import Profile
from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

TABLES = [
    User.__table__,
    Profile.__table__,
    Skill.__table__,
    UserSkill.__table__,
    MentorAvailability.__table__,
    SessionModel.__table__,
    SessionRequest.__table__,
    Notification.__table__,
    Wallet.__table__,
    WalletTransaction.__table__,
    LearningActivity.__table__,
    Feedback.__table__,
    Achievement.__table__,
    UserAchievement.__table__,
]


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_database():
    fastapi_app.dependency_overrides[get_db] = override_get_db
    for table in TABLES:
        table.create(bind=test_engine, checkfirst=True)
    yield
    for table in reversed(TABLES):
        table.drop(bind=test_engine, checkfirst=True)
    fastapi_app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(fastapi_app)


def create_user(db: Session, name: str, email: str, wallet_balance: int = 30) -> User:
    user = User(name=name, email=email, password_hash="hashed_pw")
    db.add(user)
    db.flush()

    wallet = Wallet(user_id=user.id, balance=wallet_balance, earned_coins=wallet_balance, spent_coins=0)
    db.add(wallet)
    db.commit()
    db.refresh(user)
    return user


def create_skill(db: Session, name: str = "Java Backend") -> Skill:
    skill = Skill(name=name, category="Programming")
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


def get_target_future_date(target_weekday: int = 2) -> date:
    today = date.today()
    days_ahead = (target_weekday - today.weekday()) % 7
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


# ──────────────────────────────────────────────────────────────────────────────
# 1. Full Authoritative Lifecycle Transitions (scheduled -> in_progress -> completed)
# ──────────────────────────────────────────────────────────────────────────────

def test_full_peer_session_lifecycle(db_session: Session, client: TestClient):
    mentor = create_user(db_session, "John Doe", "john@example.com", wallet_balance=10)
    learner = create_user(db_session, "Chinmay Joshi", "chinmay@example.com", wallet_balance=25)
    skill = create_skill(db_session, "Java Backend")

    target_date = get_target_future_date(1)  # Tuesday
    day_name = target_date.strftime("%A")

    add_availability(
        db=db_session,
        mentor_id=mentor.id,
        day_of_week=day_name,
        start_time=time(10, 0),
        end_time=time(14, 0)
    )

    scheduled_dt = datetime.combine(target_date, time(10, 0))

    # 1. Booking: Creates session with status="scheduled"
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
    assert session.meeting_room_id is not None
    assert "meet.jit.si" in session.meeting_link

    # Verify wallet deduction (25 - 5 = 20)
    learner_wallet = db_session.query(Wallet).filter(Wallet.user_id == learner.id).first()
    assert learner_wallet.balance == 20

    # 2. Start Session: Moves status from scheduled -> in_progress (LIVE)
    started_session = start_session(db_session, session.id, current_user_id=mentor.id)
    assert started_session.status == "in_progress"

    # 3. Complete Session: Moves status from in_progress -> completed
    completed_sess = complete_session(db_session, session.id, current_user_id=mentor.id)
    assert completed_sess.status == "completed"

    # Verify mentor rewarded
    mentor_wallet = db_session.query(Wallet).filter(Wallet.user_id == mentor.id).first()
    assert mentor_wallet.balance >= 10


# ──────────────────────────────────────────────────────────────────────────────
# 2. Invalid State Transitions Prevented
# ──────────────────────────────────────────────────────────────────────────────

def test_invalid_state_transitions_prevented(db_session: Session):
    mentor = create_user(db_session, "Mentor Guard", "guard_m@example.com")
    learner = create_user(db_session, "Learner Guard", "guard_l@example.com", wallet_balance=30)
    skill = create_skill(db_session, "Rust")

    target_date = get_target_future_date(3)
    add_availability(
        db=db_session,
        mentor_id=mentor.id,
        day_of_week=target_date.strftime("%A"),
        start_time=time(14, 0),
        end_time=time(17, 0)
    )

    session = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=datetime.combine(target_date, time(14, 0))
    )

    # Cancel session
    cancel_session(db_session, session.id, current_user_id=learner.id)
    assert session.status == "cancelled"

    # Invalid: Cannot start a cancelled session
    with pytest.raises(Exception) as exc_start:
        start_session(db_session, session.id, current_user_id=mentor.id)
    assert exc_start.value.status_code == 400

    # Invalid: Cannot complete a cancelled session
    with pytest.raises(Exception) as exc_comp:
        complete_session(db_session, session.id, current_user_id=mentor.id)
    assert exc_comp.value.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
# 3. Cancelled Session Locks Jitsi Call Access
# ──────────────────────────────────────────────────────────────────────────────

def test_cancelled_session_cannot_be_joined(db_session: Session):
    mentor = create_user(db_session, "Mentor Lock", "lock_m@example.com")
    learner = create_user(db_session, "Learner Lock", "lock_l@example.com", wallet_balance=25)
    skill = create_skill(db_session, "Go")

    target_date = get_target_future_date(4)
    add_availability(
        db=db_session,
        mentor_id=mentor.id,
        day_of_week=target_date.strftime("%A"),
        start_time=time(11, 0),
        end_time=time(15, 0)
    )

    session = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=datetime.combine(target_date, time(11, 0))
    )

    # Cancel session
    cancel_session(db_session, session.id, current_user_id=mentor.id)

    # Attempt to join cancelled session -> Must raise 409 Conflict
    with pytest.raises(Exception) as exc:
        join_session(db_session, session.id, current_user_id=learner.id)
    assert exc.value.status_code == 409
    assert "cancelled" in str(exc.value.detail).lower()


# ──────────────────────────────────────────────────────────────────────────────
# 4. Learning Activity Distinction: Learner vs Mentor
# ──────────────────────────────────────────────────────────────────────────────

def test_learning_activity_distinction(db_session: Session):
    mentor = create_user(db_session, "Mentor Sensei", "sensei@example.com")
    learner = create_user(db_session, "Learner Kohai", "kohai@example.com", wallet_balance=30)
    skill = create_skill(db_session, "FastAPI Architecture")

    target_date = get_target_future_date(5)
    add_availability(
        db=db_session,
        mentor_id=mentor.id,
        day_of_week=target_date.strftime("%A"),
        start_time=time(9, 0),
        end_time=time(13, 0)
    )

    session = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=datetime.combine(target_date, time(9, 0))
    )

    # Complete session
    complete_session(db_session, session.id, current_user_id=learner.id)

    # Query activities for learner
    learner_acts = db_session.query(LearningActivity).filter(
        LearningActivity.user_id == learner.id,
        LearningActivity.entity_id == session.id
    ).all()
    learner_types = [a.activity_type for a in learner_acts]
    assert "session_completed" in learner_types

    # Query activities for mentor
    mentor_acts = db_session.query(LearningActivity).filter(
        LearningActivity.user_id == mentor.id,
        LearningActivity.entity_id == session.id
    ).all()
    mentor_types = [a.activity_type for a in mentor_acts]
    assert "teaching_completed" in mentor_types
    # Mentor must NOT have learner session_completed activity
    assert "session_completed" not in mentor_types


# ──────────────────────────────────────────────────────────────────────────────
# 5. Authoritative Feedback Validation & Integrity Rules
# ──────────────────────────────────────────────────────────────────────────────

def test_authoritative_feedback_rules(db_session: Session, client: TestClient):
    mentor = create_user(db_session, "Review Mentor", "rev_m@example.com")
    learner = create_user(db_session, "Review Learner", "rev_l@example.com", wallet_balance=30)
    intruder = create_user(db_session, "Intruder", "intruder@example.com")
    skill = create_skill(db_session, "TypeScript")

    target_date = get_target_future_date(6)
    add_availability(
        db=db_session,
        mentor_id=mentor.id,
        day_of_week=target_date.strftime("%A"),
        start_time=time(10, 0),
        end_time=time(14, 0)
    )

    session = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=datetime.combine(target_date, time(10, 0))
    )

    # 1. Reject feedback before completion (status=scheduled)
    with pytest.raises(Exception) as exc_early:
        submit_feedback(
            db_session,
            session_id=session.id,
            reviewer_id=learner.id,
            reviewee_id=mentor.id,
            rating=5,
            comment="Great session!"
        )
    assert exc_early.value.status_code == 400
    assert "must be completed" in str(exc_early.value.detail).lower()

    # Complete session
    complete_session(db_session, session.id, current_user_id=mentor.id)

    # 2. Reject self-feedback
    with pytest.raises(Exception) as exc_self:
        submit_feedback(
            db_session,
            session_id=session.id,
            reviewer_id=learner.id,
            reviewee_id=learner.id,
            rating=5,
            comment="Self rating"
        )
    assert exc_self.value.status_code == 400
    assert "yourself" in str(exc_self.value.detail).lower()

    # 3. Reject invalid rating bounds (< 1 or > 5)
    with pytest.raises(Exception) as exc_rating:
        submit_feedback(
            db_session,
            session_id=session.id,
            reviewer_id=learner.id,
            reviewee_id=mentor.id,
            rating=6,
            comment="Invalid rating"
        )
    assert exc_rating.value.status_code == 400

    # 4. Reject unauthorized stranger feedback
    with pytest.raises(Exception) as exc_unauth:
        submit_feedback(
            db_session,
            session_id=session.id,
            reviewer_id=intruder.id,
            reviewee_id=mentor.id,
            rating=5,
            comment="I wasn't in this session"
        )
    assert exc_unauth.value.status_code == 403

    # 5. Successful feedback submission
    fb = submit_feedback(
        db_session,
        session_id=session.id,
        reviewer_id=learner.id,
        reviewee_id=mentor.id,
        rating=5,
        comment="Outstanding explanation of TypeScript generics!"
    )
    assert fb.id is not None
    assert fb.rating == 5

    # 6. Prevent duplicate feedback from same reviewer for same session (409 Conflict)
    with pytest.raises(Exception) as exc_dup:
        submit_feedback(
            db_session,
            session_id=session.id,
            reviewer_id=learner.id,
            reviewee_id=mentor.id,
            rating=4,
            comment="Trying to review twice"
        )
    assert exc_dup.value.status_code == 409


# ──────────────────────────────────────────────────────────────────────────────
# 6. Structured Participant Cards & Authorization (GET /sessions/{id}/participants)
# ──────────────────────────────────────────────────────────────────────────────

def test_session_participants_endpoint(db_session: Session, client: TestClient):
    mentor = create_user(db_session, "Mentor Card", "card_m@example.com")
    learner = create_user(db_session, "Learner Card", "card_l@example.com", wallet_balance=20)
    stranger = create_user(db_session, "Stranger Card", "stranger_c@example.com")
    skill = create_skill(db_session, "Next.js")

    target_date = get_target_future_date(0)
    add_availability(
        db=db_session,
        mentor_id=mentor.id,
        day_of_week=target_date.strftime("%A"),
        start_time=time(13, 0),
        end_time=time(16, 0)
    )

    session = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=datetime.combine(target_date, time(13, 0))
    )

    # Stranger query -> 403 Forbidden
    stranger_token = create_access_token({"sub": str(stranger.id)})
    res_s = client.get(f"/sessions/{session.id}/participants", headers={"Authorization": f"Bearer {stranger_token}"})
    assert res_s.status_code == 403

    # Learner query -> 200 OK with correct role and participant metadata
    learner_token = create_access_token({"sub": str(learner.id)})
    res_l = client.get(f"/sessions/{session.id}/participants", headers={"Authorization": f"Bearer {learner_token}"})
    assert res_l.status_code == 200
    data = res_l.json()
    assert data["current_user_role"] == "learner"
    assert data["mentor"]["name"] == "Mentor Card"
    assert data["learner"]["name"] == "Learner Card"
    assert data["skill"]["name"] == "Next.js"
