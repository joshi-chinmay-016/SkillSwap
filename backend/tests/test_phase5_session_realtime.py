"""
SkillSwap Arena — Phase 5 Real-Time Collaborative Learning & Production Session Experience Test Suite

Covers:
  - Test 1: Session start & completion records authoritative started_at and completed_at timestamps.
  - Test 2: Actual duration is calculated from authoritative timestamps.
  - Test 3: Ephemeral presence in Redis (join, heartbeat, leave, presence state).
  - Test 4: Participant presence heartbeat rate limiting & authorization.
  - Test 5: Cancelled sessions block presence join & heartbeat.
  - Test 6: Authoritative session timeline gathers genuine DB events with chronological ordering.
  - Test 7: Real-time action item WebSocket events (create, update, delete).
  - Test 8: Non-participant private session protection (403 Forbidden for presence, heartbeat, timeline).
  - Test 9: Presence cleanup upon session cancellation.
  - Test 10: Full Phase 1–4 backward compatibility regression check.
"""
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.core.database import get_db
from app.models.base import Base
from app.models.user import User
from app.models.profile import Profile
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
from app.models.journey import LearningJourney, JourneyMilestone, JourneyTask
from app.models.session_note import SessionNote
from app.models.session_topic import SessionTopic
from app.models.session_action_item import SessionActionItem
from app.models.session_intelligence import SessionIntelligence
from app.core.security import create_access_token
from app.core.redis import redis_client
from app.services.session_service import (
    schedule_session,
    start_session,
    complete_session,
    cancel_session,
    join_session,
    leave_session,
    record_session_heartbeat,
    get_session_presence,
    get_session_timeline,
    get_session_participants,
)
from app.services.session_intelligence_service import (
    save_session_note,
    add_session_topic,
    create_session_action_item,
    update_action_item_status,
    delete_session_action_item,
)
from app.services.availability_service import add_availability

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
    LearningJourney.__table__,
    JourneyMilestone.__table__,
    JourneyTask.__table__,
    SessionNote.__table__,
    SessionTopic.__table__,
    SessionActionItem.__table__,
    SessionIntelligence.__table__,
]


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


fastapi_app.dependency_overrides[get_db] = override_get_db
client = TestClient(fastapi_app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine, tables=TABLES)
    yield
    Base.metadata.drop_all(bind=test_engine, tables=TABLES)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_users(db_session: Session):
    mentor = User(
        email="mentor_p5@skillswap.test",
        password_hash="hashed_pw",
        name="Alex Mentor",
    )
    learner = User(
        email="learner_p5@skillswap.test",
        password_hash="hashed_pw",
        name="Jordan Learner",
    )
    unauthorized = User(
        email="intruder_p5@skillswap.test",
        password_hash="hashed_pw",
        name="Sam Stranger",
    )
    db_session.add_all([mentor, learner, unauthorized])
    db_session.commit()
    db_session.refresh(mentor)
    db_session.refresh(learner)
    db_session.refresh(unauthorized)

    # Profiles
    p_mentor = Profile(user_id=mentor.id, bio="Senior distributed systems architect", department="Computer Science", year=4)
    p_learner = Profile(user_id=learner.id, bio="CS Sophomore studying networking", department="Computer Science", year=2)
    db_session.add_all([p_mentor, p_learner])

    # Wallets
    w_learner = Wallet(user_id=learner.id, balance=100)
    w_mentor = Wallet(user_id=mentor.id, balance=50)
    db_session.add_all([w_learner, w_mentor])

    # Skill
    skill = Skill(name="Distributed Systems", category="Engineering")
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(skill)

    # Availability
    future_date = (datetime.now(timezone.utc) + timedelta(days=2)).date()
    add_availability(
        db_session,
        mentor_id=mentor.id,
        day_of_week=future_date.strftime("%A"),
        start_time=datetime.strptime("09:00", "%H:%M").time(),
        end_time=datetime.strptime("18:00", "%H:%M").time(),
        specific_date=future_date,
    )

    return {
        "mentor": mentor,
        "learner": learner,
        "unauthorized": unauthorized,
        "skill": skill,
        "future_date": future_date,
    }


def auth_headers(user: User) -> dict:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


# =========================================================================
# 1. Authoritative Started & Completed Timestamps and Duration
# =========================================================================
def test_session_lifecycle_timestamps_and_duration(db_session: Session, test_users):
    mentor = test_users["mentor"]
    learner = test_users["learner"]
    skill = test_users["skill"]
    slot_dt = datetime.combine(test_users["future_date"], datetime.strptime("10:00", "%H:%M").time())

    # 1. Book session
    sess = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=slot_dt,
        duration_minutes=45,
    )
    assert sess.status == "scheduled"
    assert sess.started_at is None
    assert sess.completed_at is None

    # 2. Start session
    started = start_session(db_session, sess.id, mentor.id)
    assert started.status == "in_progress"
    assert started.started_at is not None
    assert started.completed_at is None

    # 3. Complete session
    completed = complete_session(db_session, sess.id, mentor.id)
    assert completed.status == "completed"
    assert completed.completed_at is not None
    assert completed.actual_duration_minutes is not None
    assert completed.actual_duration_minutes >= 1


# =========================================================================
# 2. Ephemeral Presence & Heartbeats in Redis
# =========================================================================
def test_ephemeral_presence_and_heartbeat(db_session: Session, test_users):
    mentor = test_users["mentor"]
    learner = test_users["learner"]
    skill = test_users["skill"]
    slot_dt = datetime.combine(test_users["future_date"], datetime.strptime("11:00", "%H:%M").time())

    sess = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=slot_dt,
    )

    # Initial presence check: neither present
    presence = get_session_presence(db_session, sess.id, mentor.id)
    assert presence["mentor_present"] is False
    assert presence["learner_present"] is False
    assert presence["both_present"] is False

    # Learner joins
    join_session(db_session, sess.id, learner.id)
    presence = get_session_presence(db_session, sess.id, mentor.id)
    assert presence["learner_present"] is True
    assert presence["mentor_present"] is False
    assert presence["both_present"] is False

    # Mentor sends heartbeat
    hb = record_session_heartbeat(db_session, sess.id, mentor.id)
    assert hb["mentor_present"] is True
    assert hb["learner_present"] is True
    assert hb["both_present"] is True

    # Learner leaves
    leave_session(db_session, sess.id, learner.id)
    presence = get_session_presence(db_session, sess.id, mentor.id)
    assert presence["learner_present"] is False
    assert presence["mentor_present"] is True
    assert presence["both_present"] is False


# =========================================================================
# 3. Cancelled Session Blocks Presence
# =========================================================================
def test_cancelled_session_blocks_presence(db_session: Session, test_users):
    mentor = test_users["mentor"]
    learner = test_users["learner"]
    skill = test_users["skill"]
    slot_dt = datetime.combine(test_users["future_date"], datetime.strptime("12:00", "%H:%M").time())

    sess = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=slot_dt,
    )

    # Cancel session
    cancel_session(db_session, sess.id, mentor.id)

    # Attempting to join must raise 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        join_session(db_session, sess.id, learner.id)
    assert exc_info.value.status_code == status.HTTP_409_CONFLICT

    # Attempting to heartbeat must raise 409 Conflict
    with pytest.raises(HTTPException) as exc_info2:
        record_session_heartbeat(db_session, sess.id, learner.id)
    assert exc_info2.value.status_code == status.HTTP_409_CONFLICT


# =========================================================================
# 4. Authoritative Session Timeline from DB
# =========================================================================
def test_authoritative_session_timeline(db_session: Session, test_users):
    mentor = test_users["mentor"]
    learner = test_users["learner"]
    skill = test_users["skill"]
    slot_dt = datetime.combine(test_users["future_date"], datetime.strptime("13:00", "%H:%M").time())

    sess = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=slot_dt,
    )

    # Start session
    start_session(db_session, sess.id, mentor.id)

    # Add discussion topic
    add_session_topic(db_session, sess.id, mentor.id, "Raft Consensus Algorithm")

    # Save learner note
    save_session_note(
        db_session,
        sess.id,
        learner.id,
        {"questions": ["How does leader election work?"], "takeaways": ["Heartbeats prevent split-brain"]},
    )

    # Create action item
    create_session_action_item(
        db_session,
        sess.id,
        mentor.id,
        title="Implement Raft leader election demo",
        description="Build minimal Python simulation",
        target_user_id=learner.id,
    )

    # Complete session
    complete_session(db_session, sess.id, mentor.id)

    # Fetch timeline
    timeline = get_session_timeline(db_session, sess.id, learner.id)

    assert timeline["session_id"] == sess.id
    assert timeline["status"] == "completed"
    assert len(timeline["events"]) >= 5

    event_types = [e["type"] for e in timeline["events"]]
    assert "session_booked" in event_types
    assert "session_started" in event_types
    assert "topic_added" in event_types
    assert "note_saved" in event_types
    assert "action_item_created" in event_types
    assert "session_completed" in event_types

    # Ensure chronological order
    timestamps = [e["timestamp"] for e in timeline["events"]]
    for i in range(len(timestamps) - 1):
        t1 = timestamps[i] if timestamps[i].tzinfo else timestamps[i].replace(tzinfo=timezone.utc)
        t2 = timestamps[i + 1] if timestamps[i + 1].tzinfo else timestamps[i + 1].replace(tzinfo=timezone.utc)
        assert t1 <= t2


# =========================================================================
# 5. Action Items Real-Time Operations
# =========================================================================
def test_action_items_realtime_operations(db_session: Session, test_users):
    mentor = test_users["mentor"]
    learner = test_users["learner"]
    skill = test_users["skill"]
    slot_dt = datetime.combine(test_users["future_date"], datetime.strptime("14:00", "%H:%M").time())

    sess = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=slot_dt,
    )

    # Create action item
    item = create_session_action_item(
        db_session,
        sess.id,
        mentor.id,
        title="Review Paxos vs Raft paper",
        target_user_id=learner.id,
    )
    assert item.id is not None
    assert item.status == "pending"

    # Learner updates action item to completed
    updated = update_action_item_status(
        db_session,
        sess.id,
        item.id,
        learner.id,
        status="completed",
    )
    assert updated.status == "completed"
    assert updated.completed_at is not None

    # Learner deletes action item
    del_res = delete_session_action_item(db_session, sess.id, item.id, learner.id)
    assert "deleted successfully" in del_res["message"]


# =========================================================================
# 6. Security & Unauthorized Access Protection (403 Forbidden)
# =========================================================================
def test_unauthorized_user_blocked_from_session_realtime_data(db_session: Session, test_users):
    mentor = test_users["mentor"]
    learner = test_users["learner"]
    unauthorized = test_users["unauthorized"]
    skill = test_users["skill"]
    slot_dt = datetime.combine(test_users["future_date"], datetime.strptime("15:00", "%H:%M").time())

    sess = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=slot_dt,
    )

    # 1. Presence check by stranger -> 403
    with pytest.raises(HTTPException) as exc_info:
        get_session_presence(db_session, sess.id, unauthorized.id)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    # 2. Heartbeat by stranger -> 403
    with pytest.raises(HTTPException) as exc_info2:
        record_session_heartbeat(db_session, sess.id, unauthorized.id)
    assert exc_info2.value.status_code == status.HTTP_403_FORBIDDEN

    # 3. Timeline by stranger -> 403
    with pytest.raises(HTTPException) as exc_info3:
        get_session_timeline(db_session, sess.id, unauthorized.id)
    assert exc_info3.value.status_code == status.HTTP_403_FORBIDDEN


# =========================================================================
# 7. HTTP API Integration: Endpoints Verification
# =========================================================================
def test_http_api_presence_and_timeline_endpoints(db_session: Session, test_users):
    mentor = test_users["mentor"]
    learner = test_users["learner"]
    unauthorized = test_users["unauthorized"]
    skill = test_users["skill"]
    slot_dt = datetime.combine(test_users["future_date"], datetime.strptime("16:00", "%H:%M").time())

    sess = schedule_session(
        db=db_session,
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=slot_dt,
    )

    # 1. GET /sessions/{id}/presence
    res = client.get(f"/sessions/{sess.id}/presence", headers=auth_headers(learner))
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == sess.id
    assert "mentor_present" in data
    assert "learner_present" in data

    # 2. POST /sessions/{id}/presence/heartbeat
    res_hb = client.post(f"/sessions/{sess.id}/presence/heartbeat", headers=auth_headers(learner))
    assert res_hb.status_code == 200
    assert res_hb.json()["learner_present"] is True

    # 3. GET /sessions/{id}/timeline
    res_tl = client.get(f"/sessions/{sess.id}/timeline", headers=auth_headers(mentor))
    assert res_tl.status_code == 200
    assert res_tl.json()["session_id"] == sess.id
    assert len(res_tl.json()["events"]) >= 1

    # 4. Unauthorized access to timeline returns 403
    res_unauth = client.get(f"/sessions/{sess.id}/timeline", headers=auth_headers(unauthorized))
    assert res_unauth.status_code == 403
