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
from app.models.learning_activity import LearningActivity
from app.models.journey import LearningJourney, JourneyMilestone, JourneyTask
from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement
from app.seeds.seed_achievements import seed_initial_achievements
from app.services.learning_activity_service import record_learning_activity
from app.services.achievement_service import calculate_user_level, get_level_threshold

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
    LearningActivity.__table__.create(bind=engine, checkfirst=True)
    LearningJourney.__table__.create(bind=engine, checkfirst=True)
    Achievement.__table__.create(bind=engine, checkfirst=True)
    UserAchievement.__table__.create(bind=engine, checkfirst=True)

    db = TestingSessionLocal()
    seed_initial_achievements(db)
    db.close()

    yield

    UserAchievement.__table__.drop(bind=engine, checkfirst=True)
    Achievement.__table__.drop(bind=engine, checkfirst=True)
    LearningJourney.__table__.drop(bind=engine, checkfirst=True)
    LearningActivity.__table__.drop(bind=engine, checkfirst=True)
    User.__table__.drop(bind=engine, checkfirst=True)
    app.dependency_overrides.pop(get_db, None)


def create_test_user(email: str = "achiever@example.com") -> tuple[User, str]:
    db = TestingSessionLocal()
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        name="Achiever User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    db.close()
    return user, token


def test_unauthenticated_access():
    res = client.get("/achievements")
    assert res.status_code == 401

    res_prog = client.get("/achievements/progress")
    assert res_prog.status_code == 401


def test_empty_user_achievements():
    user, token = create_test_user("empty@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/achievements", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 6
    for ach in data:
        assert ach["unlocked"] is False
        assert ach["unlocked_at"] is None

    res_prog = client.get("/achievements/progress", headers=headers)
    assert res_prog.status_code == 200
    prog = res_prog.json()
    assert prog["level"]["current_level"] == 1
    assert prog["level"]["current_xp"] == 0
    assert prog["unlocked_count"] == 0
    assert prog["total_count"] >= 6


def test_automatic_achievement_unlock():
    user, token = create_test_user("learner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    db = TestingSessionLocal()
    record_learning_activity(
        db=db,
        user_id=user.id,
        activity_type="Session Completed",
        entity_type="session",
        entity_id=101
    )
    db.close()

    res = client.get("/achievements", headers=headers)
    assert res.status_code == 200
    achievements = res.json()

    unlocked_names = [a["name"] for a in achievements if a["unlocked"]]
    assert "First Lesson" in unlocked_names
    assert "First Session" in unlocked_names

    res_prog = client.get("/achievements/progress", headers=headers)
    assert res_prog.status_code == 200
    prog = res_prog.json()
    assert prog["unlocked_count"] == 2
    # 1 activity (10 XP) + 2 unlocked achievements (50 XP each) = 110 XP -> Level 2
    assert prog["level"]["current_xp"] == 110
    assert prog["level"]["current_level"] == 2


def test_duplicate_unlock_prevention():
    user, token = create_test_user("dup@example.com")

    db = TestingSessionLocal()
    # Perform 3 activities
    for i in range(3):
        record_learning_activity(
            db=db,
            user_id=user.id,
            activity_type="Session Completed",
            entity_type="session",
            entity_id=100 + i
        )

    user_unlocks = db.query(UserAchievement).filter(UserAchievement.user_id == user.id).all()
    first_lesson_count = len([u for u in user_unlocks if u.achievement_id == 1])
    first_session_count = len([u for u in user_unlocks if u.achievement_id == 2])
    db.close()

    # One unlock record per (user, achievement)
    assert first_lesson_count == 1
    assert first_session_count == 1


def test_level_calculation_formula():
    level_1 = calculate_user_level(0)
    assert level_1.current_level == 1
    assert level_1.current_xp == 0
    assert level_1.next_level == 2
    assert level_1.xp_to_next_level == 100
    assert level_1.progress_percentage == 0.0

    level_2 = calculate_user_level(150)
    assert level_2.current_level == 2
    assert level_2.current_xp == 150
    assert level_2.next_level == 3
    assert level_2.xp_to_next_level == 100  # 250 - 150
    assert level_2.progress_percentage == 33.3


def test_user_isolation():
    user1, token1 = create_test_user("u1@example.com")
    user2, token2 = create_test_user("u2@example.com")

    db = TestingSessionLocal()
    record_learning_activity(
        db=db,
        user_id=user1.id,
        activity_type="Session Completed",
        entity_type="session",
        entity_id=1
    )
    db.close()

    h1 = {"Authorization": f"Bearer {token1}"}
    h2 = {"Authorization": f"Bearer {token2}"}

    res1 = client.get("/achievements/progress", headers=h1).json()
    res2 = client.get("/achievements/progress", headers=h2).json()

    assert res1["unlocked_count"] >= 1
    assert res2["unlocked_count"] == 0
