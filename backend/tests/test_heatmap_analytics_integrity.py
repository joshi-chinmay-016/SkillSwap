import pytest
import datetime
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.user import User
from app.models.learning_activity import LearningActivity
from app.models.journey import LearningJourney
from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement
from app.seeds.seed_achievements import seed_initial_achievements
from app.services.learning_activity_service import (
    record_learning_activity,
    get_user_activity_heatmap,
    get_user_learning_streak,
    get_user_learning_analytics,
    invalidate_user_learning_cache
)

# SQLite in-memory test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TABLES = [
    User.__table__,
    LearningJourney.__table__,
    LearningActivity.__table__,
    Achievement.__table__,
    UserAchievement.__table__,
]


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine, tables=TABLES)
    db = TestingSessionLocal()
    seed_initial_achievements(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine, tables=TABLES)


def test_heatmap_user_isolation():
    """Ensures User A and User B heatmaps are strictly isolated and never leak across users."""
    db = TestingSessionLocal()
    try:
        user_a = User(email="user_a@test.com", password_hash="pw", name="User A")
        user_b = User(email="user_b@test.com", password_hash="pw", name="User B")
        db.add_all([user_a, user_b])
        db.commit()

        # Create 3 activities for User A on today
        for i in range(3):
            record_learning_activity(
                db,
                user_id=user_a.id,
                activity_type="task_completed",
                entity_type="journey_task",
                entity_id=i + 1,
                activity_data={"title": f"Task {i + 1}"}
            )
        db.commit()

        # Query User A heatmap
        heatmap_a = get_user_activity_heatmap(db, user_a.id)
        assert heatmap_a.total_activities == 3
        assert heatmap_a.total_active_days == 1
        assert len(heatmap_a.activity) == 1
        assert heatmap_a.activity[0].count == 3

        # Query User B heatmap (must be completely empty)
        heatmap_b = get_user_activity_heatmap(db, user_b.id)
        assert heatmap_b.total_activities == 0
        assert heatmap_b.total_active_days == 0
        assert heatmap_b.activity == []

    finally:
        db.close()


def test_honest_empty_user_state():
    """Ensures an empty user with zero activities receives honest zeros without fake/demo fallback."""
    db = TestingSessionLocal()
    try:
        fresh_user = User(email="fresh@test.com", password_hash="pw", name="Fresh User")
        db.add(fresh_user)
        db.commit()

        # Heatmap
        heatmap = get_user_activity_heatmap(db, fresh_user.id)
        assert heatmap.total_activities == 0
        assert heatmap.total_active_days == 0
        assert heatmap.activity == []

        # Streak
        streak = get_user_learning_streak(db, fresh_user.id)
        assert streak.current_streak == 0
        assert streak.longest_streak == 0
        assert streak.total_active_days == 0
        assert streak.consistency_score == 0.0

        # Analytics
        analytics = get_user_learning_analytics(db, fresh_user.id)
        assert analytics.summary.total_activities == 0
        assert analytics.summary.total_active_days == 0
        assert analytics.learning_velocity == 0.0

    finally:
        db.close()


def test_timezone_aware_date_aggregation():
    """Verifies that activities created in UTC are grouped accurately into the user's localized timezone."""
    db = TestingSessionLocal()
    try:
        user = User(email="tz_user@test.com", password_hash="pw", name="TZ User")
        db.add(user)
        db.commit()

        # Create activity at 2026-08-21 19:00:00 UTC
        # In UTC: Date is 2026-08-21
        # In Asia/Kolkata (UTC+5:30): 19:00 + 5:30 = 00:30 on 2026-08-22
        dt_utc = datetime.datetime(2026, 8, 21, 19, 0, 0, tzinfo=datetime.timezone.utc)

        act = LearningActivity(
            user_id=user.id,
            activity_type="task_completed",
            entity_type="journey_task",
            entity_id=10,
            activity_data={"title": "Midnight Task"},
            created_at=dt_utc
        )
        db.add(act)
        db.commit()

        # Query in UTC
        heatmap_utc = get_user_activity_heatmap(db, user.id, timezone_str="UTC")
        assert len(heatmap_utc.activity) == 1
        assert heatmap_utc.activity[0].date == "2026-08-21"

        # Query in Asia/Kolkata
        heatmap_ist = get_user_activity_heatmap(db, user.id, timezone_str="Asia/Kolkata")
        assert len(heatmap_ist.activity) == 1
        assert heatmap_ist.activity[0].date == "2026-08-22"

    finally:
        db.close()
