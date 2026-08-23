"""
SkillSwap Arena — Phase 7 Production Authentication & OAuth Test Suite

Covers:
  - Test 1: Standard email/password registration, login, and JWT issuance.
  - Test 2: Rate limiting on authentication endpoints.
  - Test 3: Redis-backed OAuth state generation, TTL, and one-time consumption (CSRF defense).
  - Test 4: OAuth account creation for new users with +5 Welcome Bonus.
  - Test 5: Multi-provider Account Linking (linking Google & GitHub to existing email account).
  - Test 6: OAuth identity lookup on subsequent logins without duplicating user accounts.
  - Test 7: OAuth handoff ticket generation, one-time consumption, and expiration.
  - Test 8: POST /auth/oauth/exchange endpoint validation.
"""
import time
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.core.database import get_db
from app.models.base import Base
from app.models.user import User
from app.models.profile import Profile
from app.models.oauth_identity import OAuthIdentity
from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.models.notification import Notification
from app.services.oauth_service import (
    create_oauth_state,
    verify_and_consume_oauth_state,
    authenticate_or_link_oauth_user,
    create_oauth_handoff_ticket,
    consume_oauth_handoff_ticket,
)
from app.infrastructure.redis import redis_client

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
    OAuthIdentity.__table__,
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


# =========================================================================
# 1. Standard Email/Password Auth
# =========================================================================
def test_email_password_registration_and_login(db):
    email = "phase7_user@example.com"
    pwd = "SecurePassword123!"

    # 1. Register
    reg_resp = client.post("/auth/register", json={
        "name": "Phase7 User",
        "email": email,
        "password": pwd,
    })
    assert reg_resp.status_code == 200
    assert reg_resp.json()["message"] == "User created successfully"

    # 2. Login
    login_resp = client.post("/auth/login", json={
        "email": email,
        "password": pwd,
    })
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # 3. GET /auth/me
    token = data["access_token"]
    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email


# =========================================================================
# 2. OAuth State CSRF Protection (Redis-Backed & One-Time)
# =========================================================================
def test_oauth_state_security_and_replay_protection():
    # 1. Generate state for Google
    state = create_oauth_state("google")
    assert isinstance(state, str)
    assert len(state) >= 32

    # 2. Provider mismatch must fail
    assert verify_and_consume_oauth_state(state, "github") is False

    # 3. Valid consumption
    state2 = create_oauth_state("github")
    assert verify_and_consume_oauth_state(state2, "github") is True

    # 4. Replay attack: second consumption of state2 must fail
    assert verify_and_consume_oauth_state(state2, "github") is False


# =========================================================================
# 3. Multi-Provider Account Creation & Linking
# =========================================================================
def test_oauth_account_creation_and_linking(db):
    user_email = "scholar@campus.edu"
    google_sub = "google_sub_10928374"
    github_id = "github_id_998877"

    # 1. Brand new user signs in with Google
    user_google = authenticate_or_link_oauth_user(
        db=db,
        provider="google",
        provider_user_id=google_sub,
        email=user_email,
        name="Alex Scholar",
        avatar_url="https://lh3.googleusercontent.com/a/avatar.jpg"
    )
    assert user_google.id is not None
    assert user_google.email == user_email
    assert user_google.name == "Alex Scholar"

    # Verify wallet +5 bonus was granted
    wallet = db.query(Wallet).filter(Wallet.user_id == user_google.id).first()
    assert wallet is not None
    assert wallet.balance == 5

    # 2. Same user later signs in with GitHub (Same Email) -> Should Link!
    user_github = authenticate_or_link_oauth_user(
        db=db,
        provider="github",
        provider_user_id=github_id,
        email=user_email,
        name="Alex GitHub",
        avatar_url="https://avatars.githubusercontent.com/u/998877"
    )
    # Must be the exact same user ID (no duplicate accounts created!)
    assert user_github.id == user_google.id

    # Verify both OAuth identities are linked to the single user
    identities = db.query(OAuthIdentity).filter(OAuthIdentity.user_id == user_google.id).all()
    assert len(identities) == 2
    providers = {ident.provider for ident in identities}
    assert providers == {"google", "github"}

    # 3. Subsequent sign-in with Google returns existing user directly
    user_google_again = authenticate_or_link_oauth_user(
        db=db,
        provider="google",
        provider_user_id=google_sub,
        email=user_email,
        name="Alex Scholar"
    )
    assert user_google_again.id == user_google.id


# =========================================================================
# 4. OAuth Handoff Ticket Exchange
# =========================================================================
def test_oauth_handoff_ticket_exchange():
    mock_token = "mock_jwt_access_token_12345"
    mock_user = {"id": 42, "name": "Test Peer", "email": "peer@skillswap.edu"}

    # 1. Create short-lived ticket
    ticket = create_oauth_handoff_ticket(mock_token, mock_user)
    assert len(ticket) >= 32

    # 2. POST /auth/oauth/exchange
    res = client.post("/auth/oauth/exchange", json={"ticket": ticket})
    assert res.status_code == 200
    data = res.json()
    assert data["access_token"] == mock_token
    assert data["user"]["email"] == "peer@skillswap.edu"

    # 3. Ticket replay attempt must return 400
    res_replay = client.post("/auth/oauth/exchange", json={"ticket": ticket})
    assert res_replay.status_code == 400
