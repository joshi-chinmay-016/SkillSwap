import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.journey import LearningJourney, JourneyMilestone, JourneyTask
from app.models.learning_session import LearningSession
from app.models.learning_activity import LearningActivity
from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement
from app.seeds.seed_achievements import seed_initial_achievements
from app.repositories import learning_session_repository as session_repo
from app.services import learning_session_service as session_service

from app.models.session import Session as PeerSession

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    User.__table__.create(bind=engine, checkfirst=True)
    LearningJourney.__table__.create(bind=engine, checkfirst=True)
    JourneyMilestone.__table__.create(bind=engine, checkfirst=True)
    JourneyTask.__table__.create(bind=engine, checkfirst=True)
    LearningSession.__table__.create(bind=engine, checkfirst=True)
    LearningActivity.__table__.create(bind=engine, checkfirst=True)
    Achievement.__table__.create(bind=engine, checkfirst=True)
    UserAchievement.__table__.create(bind=engine, checkfirst=True)
    PeerSession.__table__.create(bind=engine, checkfirst=True)

    db = TestingSessionLocal()
    seed_initial_achievements(db)
    db.close()

    yield

    PeerSession.__table__.drop(bind=engine, checkfirst=True)
    UserAchievement.__table__.drop(bind=engine, checkfirst=True)
    Achievement.__table__.drop(bind=engine, checkfirst=True)
    LearningActivity.__table__.drop(bind=engine, checkfirst=True)
    LearningSession.__table__.drop(bind=engine, checkfirst=True)
    JourneyTask.__table__.drop(bind=engine, checkfirst=True)
    JourneyMilestone.__table__.drop(bind=engine, checkfirst=True)
    LearningJourney.__table__.drop(bind=engine, checkfirst=True)
    User.__table__.drop(bind=engine, checkfirst=True)
    app.dependency_overrides.pop(get_db, None)


def create_test_user(email: str = "session_user@example.com") -> tuple[User, str]:
    db = TestingSessionLocal()
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        name="Session Test User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    db.close()
    return user, token


def create_test_journey(user_id: int, title: str = "Python Mastery") -> LearningJourney:
    db = TestingSessionLocal()
    journey = LearningJourney(
        user_id=user_id,
        title=title,
        target_role="Backend Developer",
        description="Learn Python for backend development",
        duration_months=3,
        status="active",
        progress_percentage=0.0,
        current_week=1,
        total_weeks=4
    )
    db.add(journey)
    db.commit()
    db.refresh(journey)
    db.close()
    return journey


# ==========================================
# Repository Unit Tests
# ==========================================

def test_repository_create_session():
    user, _ = create_test_user("repo_create@example.com")
    journey = create_test_journey(user.id)
    db = TestingSessionLocal()

    sess = session_repo.create_session(db, user.id, journey.id, "Repository Test Session")
    db.commit()
    db.refresh(sess)

    assert sess.id is not None
    assert sess.uuid is not None
    assert sess.user_id == user.id
    assert sess.journey_id == journey.id
    assert sess.title == "Repository Test Session"
    assert sess.status == "ACTIVE"
    assert sess.started_at is not None
    assert sess.ended_at is None
    db.close()


def test_repository_get_and_user_session():
    user, _ = create_test_user("repo_get@example.com")
    journey = create_test_journey(user.id)
    db = TestingSessionLocal()

    sess = session_repo.create_session(db, user.id, journey.id, "Get Session Test")
    db.commit()

    fetched = session_repo.get_session(db, sess.id)
    assert fetched is not None
    assert fetched.id == sess.id

    fetched_user = session_repo.get_user_session(db, sess.id, user.id)
    assert fetched_user is not None
    assert fetched_user.id == sess.id

    fetched_wrong_user = session_repo.get_user_session(db, sess.id, 9999)
    assert fetched_wrong_user is None
    db.close()


def test_repository_journey_sessions_ordering():
    user, _ = create_test_user("repo_order@example.com")
    journey = create_test_journey(user.id)
    db = TestingSessionLocal()

    s1 = session_repo.create_session(db, user.id, journey.id, "Session 1")
    db.commit()
    s2 = session_repo.create_session(db, user.id, journey.id, "Session 2")
    db.commit()

    sessions = session_repo.get_journey_sessions(db, journey.id)
    assert len(sessions) == 2
    # Newest first
    assert sessions[0].id == s2.id
    assert sessions[1].id == s1.id
    db.close()


def test_repository_complete_and_archive():
    user, _ = create_test_user("repo_complete@example.com")
    journey = create_test_journey(user.id)
    db = TestingSessionLocal()

    sess = session_repo.create_session(db, user.id, journey.id, "Lifecycle Session")
    db.commit()

    completed = session_repo.complete_session(db, sess)
    db.commit()
    assert completed.status == "COMPLETED"
    assert completed.ended_at is not None

    archived = session_repo.archive_session(db, sess)
    db.commit()
    assert archived.status == "ARCHIVED"
    db.close()


# ==========================================
# Service & API Integration Tests
# ==========================================

def test_create_session_api_success():
    user, token = create_test_user("api_create@example.com")
    journey = create_test_journey(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"title": "FastAPI Basics"}
    res = client.post(f"/journeys/{journey.id}/sessions", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()

    assert data["id"] is not None
    assert data["uuid"] is not None
    assert data["journey_id"] == journey.id
    assert data["title"] == "FastAPI Basics"
    assert data["status"] == "ACTIVE"
    assert data["started_at"] is not None
    assert data["ended_at"] is None


def test_create_session_invalid_journey():
    user, token = create_test_user("api_invalid_j@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/journeys/99999/sessions", json={"title": "Test"}, headers=headers)
    assert res.status_code == 404
    assert "Learning journey not found" in res.json()["detail"]


def test_create_session_unauthorized_journey():
    user1, _ = create_test_user("owner@example.com")
    user2, token2 = create_test_user("other@example.com")
    journey = create_test_journey(user1.id)
    headers = {"Authorization": f"Bearer {token2}"}

    res = client.post(f"/journeys/{journey.id}/sessions", json={"title": "Hack Attempt"}, headers=headers)
    assert res.status_code == 403
    assert "permission" in res.json()["detail"].lower()


def test_get_journey_sessions_api():
    user, token = create_test_user("get_j_sess@example.com")
    journey = create_test_journey(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    client.post(f"/journeys/{journey.id}/sessions", json={"title": "Session 1"}, headers=headers)
    client.post(f"/journeys/{journey.id}/sessions", json={"title": "Session 2"}, headers=headers)

    res = client.get(f"/journeys/{journey.id}/sessions", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["sessions"]) == 2
    assert data["sessions"][0]["title"] == "Session 2"
    assert data["sessions"][1]["title"] == "Session 1"


def test_get_single_session_api():
    user, token = create_test_user("get_sess@example.com")
    journey = create_test_journey(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post(f"/journeys/{journey.id}/sessions", json={"title": "Single Session"}, headers=headers)
    session_id = create_res.json()["id"]

    res = client.get(f"/sessions/{session_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == session_id
    assert data["title"] == "Single Session"


def test_complete_session_api_and_ecosystem_integration():
    user, token = create_test_user("complete_sess@example.com")
    journey = create_test_journey(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post(f"/journeys/{journey.id}/sessions", json={"title": "Session to Complete"}, headers=headers)
    session_id = create_res.json()["id"]

    res = client.patch(f"/sessions/{session_id}/complete", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["id"] == session_id
    assert data["status"] == "COMPLETED"
    assert data["ended_at"] is not None
    assert data["activity_created"] is True
    assert data["journey_updated"] is True
    assert data["streak_updated"] is True
    assert data["achievements_checked"] is True

    # Check Learning Activity created in DB
    db = TestingSessionLocal()
    activities = db.query(LearningActivity).filter(LearningActivity.user_id == user.id).all()
    assert len(activities) == 1
    assert activities[0].activity_type == "session_completed"
    assert activities[0].entity_type == "learning_session"
    assert activities[0].entity_id == session_id

    # Check heatmap endpoint returns total_activities = 1
    heatmap_res = client.get("/activities/heatmap", headers=headers)
    assert heatmap_res.status_code == 200
    assert heatmap_res.json()["total_activities"] == 1

    # Check achievements were evaluated (e.g. First Lesson / First Session)
    ach_res = client.get("/achievements", headers=headers)
    assert ach_res.status_code == 200
    unlocked_names = [a["name"] for a in ach_res.json() if a["unlocked"]]
    assert "First Lesson" in unlocked_names or "First Session" in unlocked_names

    db.close()


def test_complete_session_duplicate_rejection():
    user, token = create_test_user("dup_complete@example.com")
    journey = create_test_journey(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post(f"/journeys/{journey.id}/sessions", json={"title": "Session Dup"}, headers=headers)
    session_id = create_res.json()["id"]

    # First completion
    res1 = client.patch(f"/sessions/{session_id}/complete", headers=headers)
    assert res1.status_code == 200

    # Second completion (duplicate)
    res2 = client.patch(f"/sessions/{session_id}/complete", headers=headers)
    assert res2.status_code == 409
    assert "already completed" in res2.json()["detail"]


def test_archive_session_api():
    user, token = create_test_user("archive_sess@example.com")
    journey = create_test_journey(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post(f"/journeys/{journey.id}/sessions", json={"title": "Session to Archive"}, headers=headers)
    session_id = create_res.json()["id"]

    res = client.patch(f"/sessions/{session_id}/archive", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ARCHIVED"

    # Try archiving again
    res_dup = client.patch(f"/sessions/{session_id}/archive", headers=headers)
    assert res_dup.status_code == 409
    assert "already archived" in res_dup.json()["detail"]


def test_complete_archived_session_rejection():
    user, token = create_test_user("complete_archived@example.com")
    journey = create_test_journey(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post(f"/journeys/{journey.id}/sessions", json={"title": "Archived Session"}, headers=headers)
    session_id = create_res.json()["id"]

    client.patch(f"/sessions/{session_id}/archive", headers=headers)

    res = client.patch(f"/sessions/{session_id}/complete", headers=headers)
    assert res.status_code == 409
    assert "Cannot complete an archived" in res.json()["detail"]


def test_unauthorized_session_actions():
    user1, _ = create_test_user("sess_owner@example.com")
    user2, token2 = create_test_user("sess_intruder@example.com")
    journey = create_test_journey(user1.id)

    db = TestingSessionLocal()
    sess = session_repo.create_session(db, user1.id, journey.id, "Owner Session")
    db.commit()
    sess_id = sess.id
    db.close()

    headers2 = {"Authorization": f"Bearer {token2}"}

    # GET
    res_get = client.get(f"/sessions/{sess_id}", headers=headers2)
    assert res_get.status_code == 403

    # COMPLETE
    res_comp = client.patch(f"/sessions/{sess_id}/complete", headers=headers2)
    assert res_comp.status_code == 403

    # ARCHIVE
    res_arch = client.patch(f"/sessions/{sess_id}/archive", headers=headers2)
    assert res_arch.status_code == 403
