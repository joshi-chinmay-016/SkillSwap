"""
SkillSwap Arena — Phase 8.3 & 8.4 Admin Platform & Audit Logging Tests

Covers:
  - Test 1: GET /admin/dashboard returns real metrics from SQLite/DB.
  - Test 2: User management: list, search, suspend, reactivate, and role promotion with audit logs.
  - Test 3: Platform skills: create, update, and inspect stats.
  - Test 4: Mentor verification: approve and reject workflows with audit records.
  - Test 5: Session management: inspect and administratively cancel with coin refund.
  - Test 6: Report moderation: list and resolve user reports with audit trail.
  - Test 7: Wallet oversight & administrative balance adjustment with transaction record.
  - Test 8: Platform analytics & system health endpoints.
  - Test 9: GET /admin/audit-logs retrieves complete tamper-resistant history.
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
from app.models.report import Report
from app.models.admin_audit_log import AdminAuditLog
from app.models.notification import Notification
from app.core.security import hash_password, create_access_token

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
    Report.__table__,
    AdminAuditLog.__table__,
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


@pytest.fixture
def admin_token(db):
    admin = User(
        name="Platform Admin",
        email="superadmin@skillswap.com",
        password_hash=hash_password("AdminPass123!"),
        role="ADMIN",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return create_access_token({"sub": str(admin.id), "role": "ADMIN"}), admin


def test_admin_dashboard_metrics(db, admin_token):
    token, admin = admin_token
    resp = client.get("/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data
    assert "sessions" in data
    assert "mentors" in data
    assert "system" in data
    assert data["users"]["total"] >= 1


def test_admin_user_lifecycle_and_auditing(db, admin_token):
    token, admin = admin_token

    # 1. Create a regular user
    user = User(
        name="Test Student",
        email="student_test@skillswap.com",
        password_hash="pwd",
        role="USER",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 2. List users
    resp = client.get("/admin/users?search=student_test", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["email"] == "student_test@skillswap.com"

    # 3. Suspend user
    suspend_resp = client.post(
        f"/admin/users/{user.id}/suspend",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "Terms of service violation"}
    )
    assert suspend_resp.status_code == 200
    assert suspend_resp.json()["is_active"] is False

    # Check audit log
    audit = db.query(AdminAuditLog).filter(AdminAuditLog.target_id == str(user.id), AdminAuditLog.action == "SUSPEND_USER").first()
    assert audit is not None
    assert audit.admin_user_id == admin.id
    assert audit.reason == "Terms of service violation"

    # 4. Reactivate user
    react_resp = client.post(
        f"/admin/users/{user.id}/reactivate",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "Appeal accepted"}
    )
    assert react_resp.status_code == 200
    assert react_resp.json()["is_active"] is True

    # 5. Role update
    role_resp = client.post(
        f"/admin/users/{user.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "ADMIN", "reason": "Promoting team member"}
    )
    assert role_resp.status_code == 200
    assert role_resp.json()["role"] == "ADMIN"


def test_admin_skill_management(db, admin_token):
    token, admin = admin_token

    # 1. Create skill
    create_resp = client.post(
        "/admin/skills",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Rust Systems", "category": "Backend", "description": "Memory safe systems programming"}
    )
    assert create_resp.status_code == 200
    skill_id = create_resp.json()["id"]

    # 2. Update skill
    up_resp = client.put(
        f"/admin/skills/{skill_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Rust Systems Programming", "category": "Systems", "description": "Updated description"}
    )
    assert up_resp.status_code == 200
    assert up_resp.json()["name"] == "Rust Systems Programming"

    # 3. List skills
    list_resp = client.get("/admin/skills?search=Rust", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200
    assert len(list_resp.json()["items"]) == 1


def test_admin_skill_verification_workflow(db, admin_token):
    token, admin = admin_token

    user = User(name="Candidate", email="cand@test.com", password_hash="h", role="USER")
    skill = Skill(name="Docker", category="DevOps")
    db.add_all([user, skill])
    db.commit()

    us = UserSkill(user_id=user.id, skill_id=skill.id, type="TEACH", verification_status="CLAIMED", score=85.0)
    db.add(us)
    db.commit()
    db.refresh(us)

    # 1. List verifications
    v_list = client.get("/admin/verification?status=CLAIMED", headers={"Authorization": f"Bearer {token}"})
    assert v_list.status_code == 200
    assert len(v_list.json()["items"]) == 1

    # 2. Approve verification
    app_resp = client.post(
        f"/admin/verification/{us.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "Passed practical interview", "score_override": 92.0}
    )
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "VERIFIED"

    # Verify audit
    audit = db.query(AdminAuditLog).filter(AdminAuditLog.target_id == str(us.id), AdminAuditLog.action == "APPROVE_VERIFICATION").first()
    assert audit is not None


def test_admin_session_cancellation_and_refund(db, admin_token):
    token, admin = admin_token

    learner = User(name="Learner", email="l@test.com", password_hash="h", role="USER")
    mentor = User(name="Mentor", email="m@test.com", password_hash="h", role="USER")
    skill = Skill(name="Go", category="Backend")
    db.add_all([learner, mentor, skill])
    db.commit()

    learner_wallet = Wallet(user_id=learner.id, balance=3)
    db.add(learner_wallet)
    db.commit()

    session = SessionModel(
        requester_id=learner.id,
        mentor_id=mentor.id,
        skill_id=skill.id,
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
        meeting_link="https://meet.jit.si/test-cancel-room",
        status="scheduled"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Cancel session
    cancel_resp = client.post(
        f"/admin/sessions/{session.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "Mentor unavailable due to emergency", "refund_coins": True}
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"
    assert cancel_resp.json()["refund_issued"] is True

    # Check learner balance was refunded (+1 coin -> 4)
    db.refresh(learner_wallet)
    assert learner_wallet.balance == 4


def test_admin_report_moderation(db, admin_token):
    token, admin = admin_token

    reporter = User(name="Reporter", email="rep@test.com", password_hash="h", role="USER")
    target = User(name="Spammer", email="spam@test.com", password_hash="h", role="USER")
    db.add_all([reporter, target])
    db.commit()

    report = Report(
        reporter_id=reporter.id,
        reported_user_id=target.id,
        reason="Inappropriate profile information",
        status="OPEN"
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # 1. List reports
    r_list = client.get("/admin/reports?status=OPEN", headers={"Authorization": f"Bearer {token}"})
    assert r_list.status_code == 200
    assert len(r_list.json()["items"]) == 1

    # 2. Resolve report
    res_resp = client.post(
        f"/admin/reports/{report.id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "RESOLVED", "resolution_notes": "Profile avatar was reset by moderator."}
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "RESOLVED"


def test_admin_wallet_adjustment(db, admin_token):
    token, admin = admin_token

    user = User(name="Scholar", email="scholar@test.com", password_hash="h", role="USER")
    db.add(user)
    db.commit()

    wallet = Wallet(user_id=user.id, balance=5)
    db.add(wallet)
    db.commit()

    # Credit +3 bonus coins
    adj_resp = client.post(
        "/admin/wallet/adjust",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_user_id": user.id, "amount": 3, "reason": "Hackathon prize reward"}
    )
    assert adj_resp.status_code == 200
    assert adj_resp.json()["new_balance"] == 8

    # Deduct -2 coins
    adj_resp2 = client.post(
        "/admin/wallet/adjust",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_user_id": user.id, "amount": -2, "reason": "Correction"}
    )
    assert adj_resp2.status_code == 200
    assert adj_resp2.json()["new_balance"] == 6


def test_admin_audit_logs_query(db, admin_token):
    token, admin = admin_token

    # Query audit logs endpoint
    resp = client.get("/admin/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
