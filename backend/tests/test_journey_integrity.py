import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException

from app.models.base import Base
from app.models.user import User
from app.models.journey import LearningJourney, JourneyMilestone, JourneyTask
from app.models.learning_activity import LearningActivity
from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement
from app.seeds.seed_achievements import seed_initial_achievements
from app.services.journey_service import (
    create_journey,
    get_my_journeys,
    get_active_journey,
    get_journey_by_id_and_user,
    toggle_task_completion,
    update_journey
)
from app.schemas.journey import (
    LearningJourneyCreate,
    JourneyMilestoneCreate,
    JourneyTaskCreate,
    LearningJourneyUpdate
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
    JourneyMilestone.__table__,
    JourneyTask.__table__,
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


def test_journey_ownership_and_user_isolation():
    """Ensures User A and User B cannot access or modify each other's journeys or tasks."""
    db = TestingSessionLocal()
    try:
        user_a = User(email="usera@test.com", password_hash="pw", name="User A")
        user_b = User(email="userb@test.com", password_hash="pw", name="User B")
        db.add_all([user_a, user_b])
        db.commit()

        # Create journey for User A
        journey_data = LearningJourneyCreate(
            title="Backend Journey A",
            target_role="Backend Developer",
            description="Learning Backend",
            duration_months=3,
            weeks=[
                JourneyMilestoneCreate(
                    week=1,
                    topic="REST APIs",
                    goal="Build REST API",
                    tasks=[
                        JourneyTaskCreate(title="Design API schema", description="Endpoints"),
                        JourneyTaskCreate(title="Implement CRUD", description="FastAPI")
                    ]
                )
            ]
        )
        journey_a = create_journey(db, user_a.id, journey_data)
        assert journey_a.user_id == user_a.id

        task_a1 = journey_a.milestones[0].tasks[0]

        # User B attempting to access User A's journey must fail with 403
        with pytest.raises(HTTPException) as exc_info:
            get_journey_by_id_and_user(db, journey_a.id, user_b.id)
        assert exc_info.value.status_code == 403

        # User B attempting to toggle User A's task must fail with 403
        with pytest.raises(HTTPException) as exc_info:
            toggle_task_completion(db, task_a1.id, user_b.id, True)
        assert exc_info.value.status_code == 403

    finally:
        db.close()


def test_active_journey_lifecycle_and_single_active_guarantee():
    """Ensures activating a journey pauses any previously active journey for that user."""
    db = TestingSessionLocal()
    try:
        user = User(email="multi@test.com", password_hash="pw", name="Multi User")
        db.add(user)
        db.commit()

        # Create Journey 1 (Active by default)
        j1 = create_journey(db, user.id, LearningJourneyCreate(
            title="Journey 1: Python", target_role="Python Dev", description="", duration_months=1,
            weeks=[JourneyMilestoneCreate(week=1, topic="Basics", goal="Learn", tasks=[JourneyTaskCreate(title="T1")])]
        ))

        # Create Journey 2
        j2 = create_journey(db, user.id, LearningJourneyCreate(
            title="Journey 2: DevOps", target_role="DevOps Engineer", description="", duration_months=2,
            weeks=[JourneyMilestoneCreate(week=1, topic="Docker", goal="Containers", tasks=[JourneyTaskCreate(title="T2")])]
        ))

        # Activate Journey 2
        update_journey(db, j2.id, user.id, LearningJourneyUpdate(status="active"))

        db.refresh(j1)
        db.refresh(j2)

        assert j2.status == "active"
        assert j1.status == "paused"

        # Active journey query must return Journey 2
        active = get_active_journey(db, user.id)
        assert active.id == j2.id

    finally:
        db.close()


def test_authoritative_progress_and_milestone_progression():
    """Verifies that progress is calculated accurately from persisted task completion."""
    db = TestingSessionLocal()
    try:
        user = User(email="progress@test.com", password_hash="pw", name="Progress User")
        db.add(user)
        db.commit()

        # Create journey with 2 milestones (2 tasks each = 4 total tasks)
        journey = create_journey(db, user.id, LearningJourneyCreate(
            title="Full Stack Track",
            target_role="Full Stack",
            description="",
            duration_months=3,
            weeks=[
                JourneyMilestoneCreate(
                    week=1, topic="Frontend", goal="React",
                    tasks=[JourneyTaskCreate(title="Components"), JourneyTaskCreate(title="State")]
                ),
                JourneyMilestoneCreate(
                    week=2, topic="Backend", goal="FastAPI",
                    tasks=[JourneyTaskCreate(title="Routing"), JourneyTaskCreate(title="Auth")]
                )
            ]
        ))

        m1 = journey.milestones[0]
        m2 = journey.milestones[1]
        t1, t2 = m1.tasks[0], m1.tasks[1]
        t3, t4 = m2.tasks[0], m2.tasks[1]

        # Initial state: 0% progress, milestones pending
        assert journey.progress_percentage == 0.0
        assert m1.status == "pending"
        assert m2.status == "pending"

        # 1. Complete Task 1 (1/4 tasks = 25.0%)
        toggle_task_completion(db, t1.id, user.id, True)
        db.refresh(journey)
        db.refresh(m1)
        assert journey.progress_percentage == 25.0
        assert m1.status == "in_progress"

        # 2. Complete Task 2 (2/4 tasks = 50.0%, Milestone 1 completed)
        toggle_task_completion(db, t2.id, user.id, True)
        db.refresh(journey)
        db.refresh(m1)
        assert journey.progress_percentage == 50.0
        assert m1.status == "completed"

        # 3. Complete Task 3 & 4 (4/4 tasks = 100.0%, Journey completed)
        toggle_task_completion(db, t3.id, user.id, True)
        toggle_task_completion(db, t4.id, user.id, True)
        db.refresh(journey)
        db.refresh(m2)
        assert journey.progress_percentage == 100.0
        assert m2.status == "completed"
        assert journey.status == "completed"

        # Verify activities created
        activities = db.query(LearningActivity).filter(LearningActivity.user_id == user.id).all()
        act_types = [a.activity_type for a in activities]
        assert "task_completed" in act_types
        assert "milestone_completed" in act_types
        assert "journey_completed" in act_types

    finally:
        db.close()


def test_cross_journey_isolation():
    """Ensures progress in Journey A does NOT contaminate Journey B."""
    db = TestingSessionLocal()
    try:
        user = User(email="iso@test.com", password_hash="pw", name="Iso User")
        db.add(user)
        db.commit()

        j_backend = create_journey(db, user.id, LearningJourneyCreate(
            title="Backend", target_role="Backend", description="", duration_months=2,
            weeks=[JourneyMilestoneCreate(week=1, topic="SQL", goal="DB", tasks=[JourneyTaskCreate(title="Queries"), JourneyTaskCreate(title="Indexes")])]
        ))

        j_ml = create_journey(db, user.id, LearningJourneyCreate(
            title="Machine Learning", target_role="ML Engineer", description="", duration_months=2,
            weeks=[JourneyMilestoneCreate(week=1, topic="Math", goal="LinAlg", tasks=[JourneyTaskCreate(title="Vectors"), JourneyTaskCreate(title="Matrices")])]
        ))

        # Complete a task in Backend
        backend_task = j_backend.milestones[0].tasks[0]
        toggle_task_completion(db, backend_task.id, user.id, True)

        db.refresh(j_backend)
        db.refresh(j_ml)

        # Backend progressed to 50%
        assert j_backend.progress_percentage == 50.0

        # ML journey remains strictly 0%
        assert j_ml.progress_percentage == 0.0

    finally:
        db.close()
