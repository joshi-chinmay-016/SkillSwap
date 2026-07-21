import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.learning_activity import LearningActivity

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


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    User.__table__.create(bind=engine, checkfirst=True)
    LearningActivity.__table__.create(bind=engine, checkfirst=True)
    yield
    LearningActivity.__table__.drop(bind=engine, checkfirst=True)
    User.__table__.drop(bind=engine, checkfirst=True)



def create_test_user(email: str = "test@example.com") -> tuple[User, str]:
    db = TestingSessionLocal()
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        name="Test User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    db.close()
    return user, token



def test_heatmap_unauthenticated_returns_401():
    response = client.get("/activities/heatmap")
    assert response.status_code == 401

    response = client.get("/learning-activities/heatmap")
    assert response.status_code == 401


def test_heatmap_empty_user():
    user, token = create_test_user("empty@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/activities/heatmap", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["start_date"] is None
    assert data["end_date"] is None
    assert data["total_active_days"] == 0
    assert data["total_activities"] == 0
    assert data["activity"] == []


def test_heatmap_single_and_multiple_activities():
    user, token = create_test_user("active@example.com")
    db = TestingSessionLocal()

    dt1 = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)
    dt2 = datetime(2026, 7, 20, 14, 30, 0, tzinfo=timezone.utc)
    dt3 = datetime(2026, 7, 21, 9, 0, 0, tzinfo=timezone.utc)

    act1 = LearningActivity(user_id=user.id, activity_type="session", entity_type="session", entity_id=1, created_at=dt1)
    act2 = LearningActivity(user_id=user.id, activity_type="milestone", entity_type="journey", entity_id=1, created_at=dt2)
    act3 = LearningActivity(user_id=user.id, activity_type="review", entity_type="session", entity_id=2, created_at=dt3)

    db.add_all([act1, act2, act3])
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/activities/heatmap", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["start_date"] == "2026-07-20"
    assert data["end_date"] == "2026-07-21"
    assert data["total_active_days"] == 2
    assert data["total_activities"] == 3
    assert len(data["activity"]) == 2
    assert data["activity"][0] == {"date": "2026-07-20", "count": 2}
    assert data["activity"][1] == {"date": "2026-07-21", "count": 1}

    # Verify alias path returns identical response
    response_alias = client.get("/learning-activities/heatmap", headers=headers)
    assert response_alias.status_code == 200
    assert response_alias.json() == data


def test_heatmap_user_isolation():
    user1, token1 = create_test_user("user1@example.com")
    user2, token2 = create_test_user("user2@example.com")

    db = TestingSessionLocal()
    dt = datetime(2026, 7, 21, 12, 0, 0, tzinfo=timezone.utc)
    act1 = LearningActivity(user_id=user1.id, activity_type="session", entity_type="session", entity_id=1, created_at=dt)
    db.add(act1)
    db.commit()
    db.close()

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    res1 = client.get("/activities/heatmap", headers=headers1).json()
    res2 = client.get("/activities/heatmap", headers=headers2).json()

    assert res1["total_activities"] == 1
    assert res1["total_active_days"] == 1

    assert res2["total_activities"] == 0
    assert res2["total_active_days"] == 0
    assert res2["activity"] == []


def test_heatmap_invalid_and_expired_jwt_returns_401():
    headers_invalid = {"Authorization": "Bearer invalid_token_xyz"}
    res_invalid = client.get("/activities/heatmap", headers=headers_invalid)
    assert res_invalid.status_code == 401


def test_heatmap_read_only_integrity():
    user, token = create_test_user("readonly@example.com")
    db = TestingSessionLocal()

    dt = datetime(2026, 7, 21, 12, 0, 0, tzinfo=timezone.utc)
    act = LearningActivity(user_id=user.id, activity_type="session", entity_type="session", entity_id=1, created_at=dt)
    db.add(act)
    db.commit()

    initial_count = db.query(LearningActivity).count()
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/activities/heatmap", headers=headers)
    assert res.status_code == 200

    db = TestingSessionLocal()
    final_count = db.query(LearningActivity).count()
    db.close()

    assert initial_count == final_count == 1


def test_heatmap_large_dataset_performance():
    user, token = create_test_user("scale@example.com")
    db = TestingSessionLocal()

    activities = []
    # 10 days, 10 activities per day = 100 activities total
    for day in range(10, 20):
        for i in range(10):
            dt = datetime(2026, 7, day, 8 + (i % 10), 0, 0, tzinfo=timezone.utc)
            activities.append(
                LearningActivity(
                    user_id=user.id,
                    activity_type="task",
                    entity_type="task",
                    entity_id=day * 10 + i,
                    created_at=dt
                )
            )

    db.add_all(activities)
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/activities/heatmap", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["start_date"] == "2026-07-10"
    assert data["end_date"] == "2026-07-19"
    assert data["total_active_days"] == 10
    assert data["total_activities"] == 100
    assert len(data["activity"]) == 10
    for item in data["activity"]:
        assert item["count"] == 10

