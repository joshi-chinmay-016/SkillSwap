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
    yield
    LearningActivity.__table__.drop(bind=engine, checkfirst=True)
    User.__table__.drop(bind=engine, checkfirst=True)
    app.dependency_overrides.pop(get_db, None)


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


def test_analytics_unauthenticated_returns_401():
    response = client.get("/activities/analytics")
    assert response.status_code == 401

    response = client.get("/learning-activities/analytics")
    assert response.status_code == 401


def test_analytics_empty_user():
    user, token = create_test_user("empty_analytics@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/activities/analytics", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Verify weekly_activity has all 7 days with count = 0
    expected_weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    assert set(data["weekly_activity"].keys()) == set(expected_weekdays)
    for day in expected_weekdays:
        assert data["weekly_activity"][day] == 0

    # Verify monthly_activity has all 12 months with count = 0
    expected_months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    assert set(data["monthly_activity"].keys()) == set(expected_months)
    for month in expected_months:
        assert data["monthly_activity"][month] == 0

    # Verify activity_distribution has all standard types with count = 0
    expected_types = ["Task Completed", "Milestone Completed", "Journey Completed", "Session Completed"]
    assert set(data["activity_distribution"].keys()) == set(expected_types)
    for act_type in expected_types:
        assert data["activity_distribution"][act_type] == 0


def test_analytics_weekly_aggregation():
    user, token = create_test_user("weekly@example.com")
    db = TestingSessionLocal()

    # July 20, 2026 is Monday
    # July 21, 2026 is Tuesday
    # July 22, 2026 is Wednesday
    dt_monday_1 = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)
    dt_monday_2 = datetime(2026, 7, 20, 14, 0, 0, tzinfo=timezone.utc)
    dt_tuesday = datetime(2026, 7, 21, 9, 0, 0, tzinfo=timezone.utc)
    dt_wednesday = datetime(2026, 7, 22, 11, 0, 0, tzinfo=timezone.utc)

    db.add_all([
        LearningActivity(user_id=user.id, activity_type="task_completed", entity_type="task", entity_id=1, created_at=dt_monday_1),
        LearningActivity(user_id=user.id, activity_type="milestone_completed", entity_type="milestone", entity_id=2, created_at=dt_monday_2),
        LearningActivity(user_id=user.id, activity_type="journey_completed", entity_type="journey", entity_id=3, created_at=dt_tuesday),
        LearningActivity(user_id=user.id, activity_type="session_completed", entity_type="session", entity_id=4, created_at=dt_wednesday),
    ])
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/activities/analytics", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["weekly_activity"]["Monday"] == 2
    assert data["weekly_activity"]["Tuesday"] == 1
    assert data["weekly_activity"]["Wednesday"] == 1
    assert data["weekly_activity"]["Thursday"] == 0
    assert data["weekly_activity"]["Friday"] == 0
    assert data["weekly_activity"]["Saturday"] == 0
    assert data["weekly_activity"]["Sunday"] == 0


def test_analytics_monthly_aggregation():
    user, token = create_test_user("monthly@example.com")
    db = TestingSessionLocal()

    # Create activities in January, February, and July
    dt_jan = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    dt_feb1 = datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
    dt_feb2 = datetime(2026, 2, 20, 15, 0, 0, tzinfo=timezone.utc)
    dt_jul = datetime(2026, 7, 22, 9, 0, 0, tzinfo=timezone.utc)

    db.add_all([
        LearningActivity(user_id=user.id, activity_type="task_completed", entity_type="task", entity_id=1, created_at=dt_jan),
        LearningActivity(user_id=user.id, activity_type="task_completed", entity_type="task", entity_id=2, created_at=dt_feb1),
        LearningActivity(user_id=user.id, activity_type="milestone_completed", entity_type="milestone", entity_id=3, created_at=dt_feb2),
        LearningActivity(user_id=user.id, activity_type="journey_completed", entity_type="journey", entity_id=4, created_at=dt_jul),
    ])
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/activities/analytics", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["monthly_activity"]["January"] == 1
    assert data["monthly_activity"]["February"] == 2
    assert data["monthly_activity"]["March"] == 0
    assert data["monthly_activity"]["April"] == 0
    assert data["monthly_activity"]["May"] == 0
    assert data["monthly_activity"]["June"] == 0
    assert data["monthly_activity"]["July"] == 1
    assert data["monthly_activity"]["August"] == 0
    assert data["monthly_activity"]["September"] == 0
    assert data["monthly_activity"]["October"] == 0
    assert data["monthly_activity"]["November"] == 0
    assert data["monthly_activity"]["December"] == 0


def test_analytics_activity_distribution():
    user, token = create_test_user("distribution@example.com")
    db = TestingSessionLocal()

    dt = datetime(2026, 7, 22, 10, 0, 0, tzinfo=timezone.utc)

    # 3 task_completed, 2 milestone_completed, 1 journey_completed, 0 session_completed
    db.add_all([
        LearningActivity(user_id=user.id, activity_type="task_completed", entity_type="task", entity_id=1, created_at=dt),
        LearningActivity(user_id=user.id, activity_type="task_completed", entity_type="task", entity_id=2, created_at=dt),
        LearningActivity(user_id=user.id, activity_type="task_completed", entity_type="task", entity_id=3, created_at=dt),
        LearningActivity(user_id=user.id, activity_type="milestone_completed", entity_type="milestone", entity_id=4, created_at=dt),
        LearningActivity(user_id=user.id, activity_type="milestone_completed", entity_type="milestone", entity_id=5, created_at=dt),
        LearningActivity(user_id=user.id, activity_type="journey_completed", entity_type="journey", entity_id=6, created_at=dt),
    ])
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/activities/analytics", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["activity_distribution"]["Task Completed"] == 3
    assert data["activity_distribution"]["Milestone Completed"] == 2
    assert data["activity_distribution"]["Journey Completed"] == 1
    assert data["activity_distribution"]["Session Completed"] == 0


def test_analytics_user_isolation():
    user1, token1 = create_test_user("user1_analytics@example.com")
    user2, token2 = create_test_user("user2_analytics@example.com")

    db = TestingSessionLocal()
    dt = datetime(2026, 7, 22, 10, 0, 0, tzinfo=timezone.utc)

    db.add(LearningActivity(user_id=user1.id, activity_type="task_completed", entity_type="task", entity_id=1, created_at=dt))
    db.commit()
    db.close()

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    res1 = client.get("/activities/analytics", headers=headers1).json()
    res2 = client.get("/activities/analytics", headers=headers2).json()

    # User 1 should have 1 activity
    assert res1["activity_distribution"]["Task Completed"] == 1
    assert res1["weekly_activity"]["Wednesday"] == 1

    # User 2 should have 0 activities
    assert res2["activity_distribution"]["Task Completed"] == 0
    assert res2["weekly_activity"]["Wednesday"] == 0


def test_analytics_read_only_integrity():
    user, token = create_test_user("readonly_analytics@example.com")
    db = TestingSessionLocal()
    dt = datetime(2026, 7, 22, 10, 0, 0, tzinfo=timezone.utc)
    db.add(LearningActivity(user_id=user.id, activity_type="task_completed", entity_type="task", entity_id=1, created_at=dt))
    db.commit()

    initial_count = db.query(LearningActivity).count()
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/activities/analytics", headers=headers)
    assert res.status_code == 200

    db = TestingSessionLocal()
    final_count = db.query(LearningActivity).count()
    db.close()

    assert initial_count == final_count == 1


def test_user_specific_learning_analytics_independence():
    """
    Validation Test: User A created with many activities, User B created with few activities.
    Verify Dashboard, Heatmap, Streak, and Analytics return completely independent values.
    """
    user_a, token_a = create_test_user("usera@example.com")
    user_b, token_b = create_test_user("userb@example.com")

    db = TestingSessionLocal()
    dt1 = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)
    dt2 = datetime(2026, 7, 21, 11, 0, 0, tzinfo=timezone.utc)
    dt3 = datetime(2026, 7, 22, 12, 0, 0, tzinfo=timezone.utc)

    # User A: 5 activities
    db.add_all([
        LearningActivity(user_id=user_a.id, activity_type="task_completed", entity_type="task", entity_id=1, created_at=dt1),
        LearningActivity(user_id=user_a.id, activity_type="milestone_completed", entity_type="milestone", entity_id=2, created_at=dt1),
        LearningActivity(user_id=user_a.id, activity_type="journey_completed", entity_type="journey", entity_id=3, created_at=dt2),
        LearningActivity(user_id=user_a.id, activity_type="session_completed", entity_type="session", entity_id=4, created_at=dt2),
        LearningActivity(user_id=user_a.id, activity_type="task_completed", entity_type="task", entity_id=5, created_at=dt3),
    ])

    # User B: 1 activity
    db.add(LearningActivity(user_id=user_b.id, activity_type="task_completed", entity_type="task", entity_id=10, created_at=dt1))
    db.commit()
    db.close()

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Analytics Check
    res_a_analytics = client.get("/activities/analytics", headers=headers_a).json()
    res_b_analytics = client.get("/activities/analytics", headers=headers_b).json()

    assert res_a_analytics["summary"]["total_activities"] == 5
    assert res_b_analytics["summary"]["total_activities"] == 1

    assert res_a_analytics["summary"]["total_active_days"] == 3
    assert res_b_analytics["summary"]["total_active_days"] == 1

    # 2. Heatmap Check
    res_a_heatmap = client.get("/activities/heatmap", headers=headers_a).json()
    res_b_heatmap = client.get("/activities/heatmap", headers=headers_b).json()

    assert res_a_heatmap["total_activities"] == 5
    assert res_b_heatmap["total_activities"] == 1

    # 3. Streak Check
    res_a_streak = client.get("/activities/streak", headers=headers_a).json()
    res_b_streak = client.get("/activities/streak", headers=headers_b).json()

    assert res_a_streak["total_active_days"] == 3
    assert res_b_streak["total_active_days"] == 1


def test_analytics_ignores_attempted_user_id_override():
    """
    Security Test: Requesting /activities/analytics?user_id=X with User B's token
    must ALWAYS return User B's analytics, completely ignoring the user_id query parameter.
    """
    user_a, token_a = create_test_user("user_override_a@example.com")
    user_b, token_b = create_test_user("user_override_b@example.com")

    db = TestingSessionLocal()
    dt = datetime(2026, 7, 22, 10, 0, 0, tzinfo=timezone.utc)
    db.add(LearningActivity(user_id=user_a.id, activity_type="task_completed", entity_type="task", entity_id=1, created_at=dt))
    db.commit()
    db.close()

    # User B attempts to view User A's analytics by passing user_id=user_a.id in query params
    headers_b = {"Authorization": f"Bearer {token_b}"}
    res = client.get(f"/activities/analytics?user_id={user_a.id}", headers=headers_b).json()

    # Must return User B's zero activities, not User A's activity!
    assert res["summary"]["total_activities"] == 0

