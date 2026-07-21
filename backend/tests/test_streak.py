import pytest
from datetime import datetime, date, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.learning_activity import LearningActivity
from app.services.learning_activity_service import get_user_learning_streak

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


def test_streak_unauthenticated_returns_401():
    response = client.get("/activities/streak")
    assert response.status_code == 401

    response = client.get("/learning-activities/streak")
    assert response.status_code == 401


def test_streak_empty_user():
    user, token = create_test_user("empty_streak@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/activities/streak", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["current_streak"] == 0
    assert data["longest_streak"] == 0
    assert data["total_active_days"] == 0
    assert data["last_active_date"] is None
    assert data["consistency_score"] == 0.0
    assert data["current_milestone"] is None
    assert data["next_milestone"] == {"name": "Getting Started", "threshold": 3}
    assert data["remaining_days"] == 3
    assert data["progress_percentage"] == 0.0



def test_streak_single_active_day_today():
    user, token = create_test_user("today_streak@example.com")
    db = TestingSessionLocal()

    now = datetime.now(timezone.utc)
    act = LearningActivity(
        user_id=user.id,
        activity_type="task",
        entity_type="task",
        entity_id=1,
        created_at=now
    )
    db.add(act)
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/activities/streak", headers=headers)
    assert response.status_code == 200
    data = response.json()

    today_str = str(now.date())
    assert data["current_streak"] == 1
    assert data["longest_streak"] == 1
    assert data["total_active_days"] == 1
    assert data["last_active_date"] == today_str


def test_streak_active_yesterday_not_today():
    user, token = create_test_user("yesterday_streak@example.com")
    db = TestingSessionLocal()

    today = date.today()
    yesterday = today - timedelta(days=1)
    dt = datetime(yesterday.year, yesterday.month, yesterday.day, 12, 0, 0, tzinfo=timezone.utc)

    act = LearningActivity(
        user_id=user.id,
        activity_type="session",
        entity_type="session",
        entity_id=1,
        created_at=dt
    )
    db.add(act)
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/activities/streak", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["current_streak"] == 1  # Streak is still active because yesterday was active!
    assert data["longest_streak"] == 1
    assert data["total_active_days"] == 1
    assert data["last_active_date"] == str(yesterday)


def test_streak_consecutive_days_and_longest():
    user, token = create_test_user("consecutive@example.com")
    db = TestingSessionLocal()

    ref_date = date(2026, 7, 22)

    # Sequence 1: 3 consecutive days (July 10, 11, 12) -> longest = 3
    # Sequence 2: 4 consecutive days (July 20, 21, 22) -> current = 3 (if ref_date is July 22), longest = 4
    dates_to_add = [
        date(2026, 7, 10),
        date(2026, 7, 11),
        date(2026, 7, 12),
        date(2026, 7, 20),
        date(2026, 7, 21),
        date(2026, 7, 22),
    ]

    for d in dates_to_add:
        dt = datetime(d.year, d.month, d.day, 10, 0, 0, tzinfo=timezone.utc)
        db.add(LearningActivity(
            user_id=user.id,
            activity_type="task",
            entity_type="task",
            entity_id=d.day,
            created_at=dt
        ))

    db.commit()

    # Test direct service logic with fixed reference date (July 22)
    streak_res = get_user_learning_streak(db, user.id, ref_today=ref_date)
    assert streak_res.current_streak == 3  # July 20, 21, 22
    assert streak_res.longest_streak == 3  # Two streaks of length 3: [10,11,12] and [20,21,22]
    assert streak_res.total_active_days == 6
    assert streak_res.last_active_date == "2026-07-22"

    db.close()


def test_streak_broken_streak():
    user, token = create_test_user("broken@example.com")
    db = TestingSessionLocal()

    ref_date = date(2026, 7, 22)

    # Activity on July 18 & 19 (length 2), gap on July 20 & 21 & 22 -> current_streak = 0, longest_streak = 2
    dates = [date(2026, 7, 18), date(2026, 7, 19)]
    for d in dates:
        dt = datetime(d.year, d.month, d.day, 10, 0, 0, tzinfo=timezone.utc)
        db.add(LearningActivity(
            user_id=user.id,
            activity_type="task",
            entity_type="task",
            entity_id=d.day,
            created_at=dt
        ))
    db.commit()

    streak_res = get_user_learning_streak(db, user.id, ref_today=ref_date)
    assert streak_res.current_streak == 0
    assert streak_res.longest_streak == 2
    assert streak_res.total_active_days == 2
    assert streak_res.last_active_date == "2026-07-19"

    db.close()


def test_streak_multiple_activities_same_day():
    user, token = create_test_user("same_day@example.com")
    db = TestingSessionLocal()

    ref_date = date(2026, 7, 22)

    # 5 activities on July 22 -> total_active_days = 1
    for i in range(5):
        dt = datetime(2026, 7, 22, 8 + i, 0, 0, tzinfo=timezone.utc)
        db.add(LearningActivity(
            user_id=user.id,
            activity_type=f"task_{i}",
            entity_type="task",
            entity_id=i,
            created_at=dt
        ))
    db.commit()

    streak_res = get_user_learning_streak(db, user.id, ref_today=ref_date)
    assert streak_res.current_streak == 1
    assert streak_res.longest_streak == 1
    assert streak_res.total_active_days == 1
    assert streak_res.last_active_date == "2026-07-22"

    db.close()


def test_streak_user_isolation():
    user1, token1 = create_test_user("streak_u1@example.com")
    user2, token2 = create_test_user("streak_u2@example.com")

    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    db.add(LearningActivity(user_id=user1.id, activity_type="task", entity_type="task", entity_id=1, created_at=now))
    db.commit()
    db.close()

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    res1 = client.get("/activities/streak", headers=headers1).json()
    res2 = client.get("/activities/streak", headers=headers2).json()

    assert res1["total_active_days"] == 1
    assert res1["current_streak"] == 1

    assert res2["total_active_days"] == 0
    assert res2["current_streak"] == 0
    assert res2["last_active_date"] is None


def test_streak_read_only_integrity():
    user, token = create_test_user("readonly_streak@example.com")
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    db.add(LearningActivity(user_id=user.id, activity_type="task", entity_type="task", entity_id=1, created_at=now))
    db.commit()

    initial_count = db.query(LearningActivity).count()
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/activities/streak", headers=headers)
    assert res.status_code == 200

    db = TestingSessionLocal()
    final_count = db.query(LearningActivity).count()
    db.close()

    assert initial_count == final_count == 1


def test_streak_consistency_score_and_milestones():
    user, token = create_test_user("milestones@example.com")
    db = TestingSessionLocal()
    ref_date = date(2026, 7, 22)

    # Add 18 consecutive active days from July 5 to July 22
    # First activity: July 5. Ref date: July 22 -> 18 days span.
    # Active days: 18. Consistency = (18 / 18) * 100 = 100.0%
    for i in range(18):
        d = date(2026, 7, 5) + timedelta(days=i)
        dt = datetime(d.year, d.month, d.day, 10, 0, 0, tzinfo=timezone.utc)
        db.add(LearningActivity(
            user_id=user.id,
            activity_type="task",
            entity_type="task",
            entity_id=i,
            created_at=dt
        ))
    db.commit()

    streak_res = get_user_learning_streak(db, user.id, ref_today=ref_date)
    assert streak_res.current_streak == 18
    assert streak_res.total_active_days == 18
    assert streak_res.consistency_score == 100.0
    assert streak_res.current_milestone.name == "Momentum Builder"
    assert streak_res.current_milestone.threshold == 15
    assert streak_res.next_milestone.name == "Dedicated Learner"
    assert streak_res.next_milestone.threshold == 30
    assert streak_res.remaining_days == 12  # 30 - 18
    # Progress: (18 - 15) / (30 - 15) * 100 = 3 / 15 * 100 = 20.0%
    assert streak_res.progress_percentage == 20.0

    db.close()


def test_streak_consistency_score_gap_days():
    user, token = create_test_user("consistency_gap@example.com")
    db = TestingSessionLocal()
    ref_date = date(2026, 7, 22)

    # First activity July 13 (10 days span up to July 22)
    # Active on July 13 and July 22 (2 days out of 10)
    # Consistency = (2 / 10) * 100 = 20.0%
    d1 = datetime(2026, 7, 13, 10, 0, 0, tzinfo=timezone.utc)
    d2 = datetime(2026, 7, 22, 10, 0, 0, tzinfo=timezone.utc)
    db.add_all([
        LearningActivity(user_id=user.id, activity_type="t1", entity_type="task", entity_id=1, created_at=d1),
        LearningActivity(user_id=user.id, activity_type="t2", entity_type="task", entity_id=2, created_at=d2)
    ])
    db.commit()

    streak_res = get_user_learning_streak(db, user.id, ref_today=ref_date)
    assert streak_res.total_active_days == 2
    assert streak_res.consistency_score == 20.0

    db.close()


def test_streak_max_milestone_exceeded():
    user, token = create_test_user("max_milestone@example.com")
    db = TestingSessionLocal()
    ref_date = date(2026, 7, 22)

    # 365 consecutive active days
    start_d = ref_date - timedelta(days=364)
    for i in range(365):
        d = start_d + timedelta(days=i)
        dt = datetime(d.year, d.month, d.day, 10, 0, 0, tzinfo=timezone.utc)
        db.add(LearningActivity(
            user_id=user.id,
            activity_type="task",
            entity_type="task",
            entity_id=i,
            created_at=dt
        ))
    db.commit()

    streak_res = get_user_learning_streak(db, user.id, ref_today=ref_date)
    assert streak_res.current_streak == 365
    assert streak_res.current_milestone.name == "Legendary Learner"
    assert streak_res.current_milestone.threshold == 365
    assert streak_res.next_milestone is None
    assert streak_res.remaining_days == 0
    assert streak_res.progress_percentage == 100.0

    db.close()

