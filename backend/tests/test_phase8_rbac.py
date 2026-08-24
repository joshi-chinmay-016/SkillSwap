"""
SkillSwap Arena — Phase 8.1 Platform Authorization & RBAC Foundation Tests

Covers:
  - Test 1: Standard registration defaults to role USER and is_active True.
  - Test 2: Privilege escalation prevention: frontend cannot inject role=ADMIN in registration.
  - Test 3: Unauthenticated request to admin-guarded route returns 401.
  - Test 4: Authenticated non-admin (USER) request to admin-guarded route returns 403 Forbidden.
  - Test 5: Authenticated ADMIN user successfully accesses admin-guarded route (200 OK).
  - Test 6: Suspended user (is_active=False) is denied access with 403 on protected routes.
  - Test 7: Suspended user cannot log in via email/password.
  - Test 8: GET /auth/me returns authoritative role and is_active flags.
"""
import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.core.database import get_db
from app.models.base import Base
from app.models.user import User
from app.models.profile import Profile
from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.models.notification import Notification
from app.dependencies.auth_guards import require_admin, require_active_user
from app.core.security import hash_password, create_access_token

# Test database in memory
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
    Wallet.__table__,
    WalletTransaction.__table__,
    Notification.__table__,
]

# Create a test router to verify require_admin guard
admin_mock_router = APIRouter(prefix="/test-admin", tags=["Test Admin"])

@admin_mock_router.get("/protected")
def admin_protected_endpoint(admin_user: User = Depends(require_admin)):
    return {"message": "Admin access granted", "admin_id": admin_user.id, "role": admin_user.role}

fastapi_app.include_router(admin_mock_router)


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


def test_registration_defaults_to_user_role(db):
    email = "new_peer@skillswap.com"
    resp = client.post("/auth/register", json={
        "name": "New Peer",
        "email": email,
        "password": "Password123!",
    })
    assert resp.status_code == 200

    user = db.query(User).filter(User.email == email).first()
    assert user is not None
    assert user.role == "USER"
    assert user.is_active is True


def test_privilege_escalation_attempt_ignored(db):
    email = "attacker@skillswap.com"
    # Attacker tries to inject role="ADMIN" or is_admin=True in register body
    resp = client.post("/auth/register", json={
        "name": "Attacker",
        "email": email,
        "password": "Password123!",
        "role": "ADMIN",
        "is_admin": True,
    })
    assert resp.status_code == 200

    user = db.query(User).filter(User.email == email).first()
    assert user is not None
    # Server authority must strictly enforce USER role
    assert user.role == "USER"


def test_unauthenticated_admin_access_returns_401():
    resp = client.get("/test-admin/protected")
    assert resp.status_code == 401


def test_standard_user_admin_access_returns_403(db):
    user = User(
        name="Regular Student",
        email="student@skillswap.com",
        password_hash=hash_password("Pass123!"),
        role="USER",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": "USER"})
    resp = client.get(
        "/test-admin/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403
    assert "Administrator privileges required" in resp.json()["detail"]


def test_admin_user_access_returns_200(db):
    admin = User(
        name="Platform Administrator",
        email="admin@skillswap.com",
        password_hash=hash_password("AdminPass123!"),
        role="ADMIN",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    token = create_access_token({"sub": str(admin.id), "role": "ADMIN"})
    resp = client.get(
        "/test-admin/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Admin access granted"
    assert data["role"] == "ADMIN"


def test_suspended_user_is_blocked(db):
    suspended_user = User(
        name="Suspended Account",
        email="suspended@skillswap.com",
        password_hash=hash_password("Pass123!"),
        role="USER",
        is_active=False,
    )
    db.add(suspended_user)
    db.commit()
    db.refresh(suspended_user)

    token = create_access_token({"sub": str(suspended_user.id), "role": "USER"})
    resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403
    assert "Account is suspended" in resp.json()["detail"]


def test_suspended_user_cannot_login(db):
    user = User(
        name="Inactive User",
        email="inactive@skillswap.com",
        password_hash=hash_password("Pass123!"),
        role="USER",
        is_active=False,
    )
    db.add(user)
    db.commit()

    resp = client.post("/auth/login", json={
        "email": "inactive@skillswap.com",
        "password": "Pass123!",
    })
    assert resp.status_code == 401
    assert "Account is suspended" in resp.json()["detail"]


def test_auth_me_returns_authoritative_role_and_status(db):
    user = User(
        name="Profile Check",
        email="check@skillswap.com",
        password_hash=hash_password("Pass123!"),
        role="USER",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = Profile(user_id=user.id, avatar_url="https://avatar.url/test.svg")
    db.add(profile)
    db.commit()

    token = create_access_token({"sub": str(user.id), "role": "USER"})
    resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "USER"
    assert data["is_active"] is True
    assert data["email"] == "check@skillswap.com"
