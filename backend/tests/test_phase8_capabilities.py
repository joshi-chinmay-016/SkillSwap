"""
SkillSwap Arena — Phase 8.2 Teaching / Learning Capability Model Tests

Covers:
  - Test 1: User can simultaneously have LEARN skills and verified TEACH skills without role separation.
  - Test 2: Unverified TEACH skill does not grant active can_teach capability until verified.
  - Test 3: Same user can act as mentor in one session and learner in another session.
  - Test 4: Capability service accurately aggregates contextual sessions and skill statuses.
  - Test 5: GET /profiles/me/capabilities and GET /profiles/{id}/capabilities return valid data.
"""
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.core.database import get_db
from app.models.base import Base
from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.models.session import Session as SessionModel
from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.models.notification import Notification
from app.core.security import hash_password, create_access_token
from app.services.capability_service import get_user_capabilities, is_verified_to_teach

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
    SessionModel.__table__,
    Wallet.__table__,
    WalletTransaction.__table__,
    Notification.__table__,
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
    fastapi_app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine, tables=TABLES)
    yield
    Base.metadata.drop_all(bind=test_engine, tables=TABLES)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_simultaneous_teaching_and_learning_capabilities(db):
    user = User(
        name="Alex River",
        email="alex@skillswap.com",
        password_hash=hash_password("Pass123!"),
        role="USER",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    skill_python = Skill(name="Python", category="Backend")
    skill_k8s = Skill(name="Kubernetes", category="DevOps")
    skill_react = Skill(name="React", category="Frontend")
    db.add_all([skill_python, skill_k8s, skill_react])
    db.commit()

    # 1. Verified teaching skill (Python)
    us_python = UserSkill(
        user_id=user.id,
        skill_id=skill_python.id,
        type="TEACH",
        verification_status="VERIFIED",
        score=95.0,
        verified_at=datetime.now(timezone.utc),
    )
    # 2. Pending teaching skill (React)
    us_react = UserSkill(
        user_id=user.id,
        skill_id=skill_react.id,
        type="TEACH",
        verification_status="CLAIMED",
    )
    # 3. Learning skill (Kubernetes)
    us_k8s = UserSkill(
        user_id=user.id,
        skill_id=skill_k8s.id,
        type="LEARN",
    )
    db.add_all([us_python, us_react, us_k8s])
    db.commit()

    caps = get_user_capabilities(db, user.id)
    assert caps is not None
    assert caps["can_teach"] is True
    assert caps["can_learn"] is True
    assert len(caps["verified_teaching_skills"]) == 1
    assert caps["verified_teaching_skills"][0]["skill_name"] == "Python"
    assert len(caps["pending_teaching_skills"]) == 1
    assert caps["pending_teaching_skills"][0]["skill_name"] == "React"
    assert len(caps["learning_skills"]) == 1
    assert caps["learning_skills"][0]["skill_name"] == "Kubernetes"

    assert is_verified_to_teach(db, user.id, skill_python.id) is True
    assert is_verified_to_teach(db, user.id, skill_react.id) is False


def test_contextual_dual_session_roles(db):
    # User A (Alex) and User B (Jordan)
    user_a = User(name="Alex", email="alex@test.com", password_hash="h", role="USER")
    user_b = User(name="Jordan", email="jordan@test.com", password_hash="h", role="USER")
    db.add_all([user_a, user_b])
    db.commit()

    skill = Skill(name="FastAPI", category="Backend")
    db.add(skill)
    db.commit()

    # Session 1: Alex teaches Jordan (Alex is Mentor, Jordan is Learner)
    session_1 = SessionModel(
        requester_id=user_b.id,
        mentor_id=user_a.id,
        skill_id=skill.id,
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
        meeting_link="https://meet.jit.si/skillswap-room-1",
        status="completed"
    )
    # Session 2: Jordan teaches Alex (Jordan is Mentor, Alex is Learner)
    session_2 = SessionModel(
        requester_id=user_a.id,
        mentor_id=user_b.id,
        skill_id=skill.id,
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=2),
        meeting_link="https://meet.jit.si/skillswap-room-2",
        status="completed"
    )
    db.add_all([session_1, session_2])
    db.commit()

    caps_a = get_user_capabilities(db, user_a.id)
    assert caps_a["session_history"]["as_mentor_count"] == 1
    assert caps_a["session_history"]["as_learner_count"] == 1
    assert caps_a["session_history"]["total_sessions"] == 2

    caps_b = get_user_capabilities(db, user_b.id)
    assert caps_b["session_history"]["as_mentor_count"] == 1
    assert caps_b["session_history"]["as_learner_count"] == 1
    assert caps_b["session_history"]["total_sessions"] == 2


def test_capabilities_api_endpoints(db):
    user = User(
        name="Sam Reader",
        email="sam@test.com",
        password_hash=hash_password("Pass123!"),
        role="USER"
    )
    db.add(user)
    db.commit()

    token = create_access_token({"sub": str(user.id), "role": "USER"})

    # GET /profiles/me/capabilities
    resp = client.get("/profiles/me/capabilities", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == user.id
    assert data["can_learn"] is True

    # GET /profiles/{user_id}/capabilities
    resp2 = client.get(f"/profiles/{user.id}/capabilities")
    assert resp2.status_code == 200
    assert resp2.json()["email"] == "sam@test.com"
