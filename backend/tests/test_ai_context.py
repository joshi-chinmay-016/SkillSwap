"""
Unit and integration tests for the Learning AI Profile system (AIContext).

Tests cover:
  1. Service rebuild aggregation engine (completed sessions, summaries, journeys, styles).
  2. Service manual updates (learning_interests, learning_style).
  3. API endpoints: GET, POST /regenerate, PATCH /users/me/context.
  4. Automatic profile rebuild trigger on session summary creation.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.models.user import User
from app.models.journey import LearningJourney
from app.models.learning_session import LearningSession
from app.models.session_summary import SessionSummary
from app.models.ai_context import AIContext
from app.schemas.ai_context import AIContextUpdate
from app.services.ai_context_service import (
    get_user_ai_context,
    rebuild_user_ai_context,
    update_user_ai_context,
)
from app.services import session_summary_service
from app.schemas.session_summary import SessionSummaryCreate

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


@pytest.fixture(autouse=True)
def setup_db():
    """Create fresh tables for every test."""
    app.dependency_overrides[get_db] = override_get_db
    User.__table__.create(bind=engine, checkfirst=True)
    LearningJourney.__table__.create(bind=engine, checkfirst=True)
    LearningSession.__table__.create(bind=engine, checkfirst=True)
    SessionSummary.__table__.create(bind=engine, checkfirst=True)
    AIContext.__table__.create(bind=engine, checkfirst=True)

    db = TestingSessionLocal()
    yield db
    db.close()

    AIContext.__table__.drop(bind=engine, checkfirst=True)
    SessionSummary.__table__.drop(bind=engine, checkfirst=True)
    LearningSession.__table__.drop(bind=engine, checkfirst=True)
    LearningJourney.__table__.drop(bind=engine, checkfirst=True)
    User.__table__.drop(bind=engine, checkfirst=True)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(setup_db):
    db = setup_db
    user = User(
        id=1,
        email="learner@example.com",
        password_hash="hashed_pw",
        name="AI Learner",
    )
    db.add(user)
    db.commit()

    def override_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_get_current_user
    return user


class TestAIContextService:

    def test_get_user_ai_context_empty(self, setup_db, test_user):
        db = setup_db
        ctx = get_user_ai_context(db, test_user.id)
        assert ctx is None

    def test_rebuild_user_ai_context_no_data(self, setup_db, test_user):
        db = setup_db
        ctx = rebuild_user_ai_context(db, test_user.id)
        db.commit()

        assert ctx is not None
        assert ctx.user_id == test_user.id
        assert ctx.completed_sessions == 0
        assert ctx.strong_topics == []
        assert ctx.weak_topics == []
        assert "not yet completed any sessions" in ctx.overall_summary

    def test_rebuild_user_ai_context_with_sessions_and_summaries(self, setup_db, test_user):
        db = setup_db

        # 1. Create a journey
        journey = LearningJourney(
            user_id=test_user.id,
            title="Mastering Data Structures",
            target_role="Backend Developer",
            status="active",
        )
        db.add(journey)
        db.commit()

        # 2. Create completed learning sessions
        s1 = LearningSession(
            user_id=test_user.id,
            journey_id=journey.id,
            title="Binary Search Deep Dive",
            status="COMPLETED",
        )
        s2 = LearningSession(
            user_id=test_user.id,
            journey_id=journey.id,
            title="Graph Algorithms",
            status="COMPLETED",
        )
        db.add_all([s1, s2])
        db.commit()

        # 3. Create session summaries
        sum1 = SessionSummary(
            session_id=s1.id,
            summary="Learned binary search trees.",
            key_takeaways=["Binary Search", "O(log n)"],
            strengths=["Binary Search", "Divide and Conquer"],
            weaknesses=["Edge Cases"],
            follow_up_topics=["AVL Trees", "Red-Black Trees"],
        )
        sum2 = SessionSummary(
            session_id=s2.id,
            summary="Learned BFS and DFS.",
            key_takeaways=["Graph Traversal", "BFS"],
            strengths=["Binary Search", "Graph Traversal"],
            weaknesses=["Edge Cases", "Dijkstra Algorithm"],
            follow_up_topics=["Topological Sort"],
        )
        db.add_all([sum1, sum2])
        db.commit()

        # 4. Rebuild AI context
        ctx = rebuild_user_ai_context(db, test_user.id)
        db.commit()

        assert ctx.completed_sessions == 2
        # Binary Search appeared in both summaries, should be first
        assert ctx.strong_topics[0] == "Binary Search"
        assert "Edge Cases" in ctx.weak_topics
        assert "AVL Trees" in ctx.recommended_topics
        assert "Backend Developer" in ctx.learning_interests
        assert ctx.context_version == 1

    def test_update_user_ai_context(self, setup_db, test_user):
        db = setup_db

        # Create initial context
        ctx = rebuild_user_ai_context(db, test_user.id)
        db.commit()
        initial_version = ctx.context_version

        # Update manual fields
        update_data = AIContextUpdate(
            learning_interests=["Distributed Systems", "Rust"],
            learning_style="Prefers hands-on coding exercises with minimal theory.",
        )
        updated = update_user_ai_context(db, test_user.id, update_data)
        db.commit()

        assert updated.context_version == initial_version + 1
        assert "Distributed Systems" in updated.learning_interests
        assert "Rust" in updated.learning_interests
        assert "hands-on coding" in updated.learning_style


class TestAIContextAPI:

    def test_get_context_404(self, test_user):
        client = TestClient(app)
        response = client.get("/users/me/context")
        assert response.status_code == 404

    def test_regenerate_context_and_get(self, setup_db, test_user):
        client = TestClient(app)

        # Regenerate profile
        res = client.post("/users/me/context/regenerate")
        assert res.status_code == 200
        data = res.json()
        assert data["user_id"] == test_user.id
        assert data["context_version"] == 1
        assert data["completed_sessions"] == 0

        # Now GET returns 200
        get_res = client.get("/users/me/context")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == data["id"]

    def test_patch_context(self, setup_db, test_user):
        client = TestClient(app)

        # Regenerate profile first
        client.post("/users/me/context/regenerate")

        # Patch fields
        patch_res = client.patch(
            "/users/me/context",
            json={
                "learning_interests": ["System Design", "Cloud Native"],
                "learning_style": "Visual learner with diagrammatic summaries.",
            },
        )
        assert patch_res.status_code == 200
        data = patch_res.json()
        assert data["learning_interests"] == ["System Design", "Cloud Native"]
        assert data["learning_style"] == "Visual learner with diagrammatic summaries."
        assert data["context_version"] == 2


class TestAutoRebuildTrigger:

    def test_summary_creation_triggers_profile_rebuild(self, setup_db, test_user):
        db = setup_db

        # Create active journey & session
        j = LearningJourney(user_id=test_user.id, title="Python Mastery", target_role="Python Dev")
        db.add(j)
        db.commit()

        session = LearningSession(user_id=test_user.id, journey_id=j.id, title="Decorators", status="COMPLETED")
        db.add(session)
        db.commit()

        # Context does not exist before summary
        assert get_user_ai_context(db, test_user.id) is None

        # Create session summary via service
        summary_data = SessionSummaryCreate(
            summary="Mastered Python decorators.",
            key_takeaways=["Decorators", "Wrappers"],
            strengths=["Decorators"],
            weaknesses=["Closure scope"],
            follow_up_topics=["Generators"],
        )
        session_summary_service.create_summary(db, session.id, test_user.id, summary_data)

        # Profile should be automatically created!
        ctx = get_user_ai_context(db, test_user.id)
        assert ctx is not None
        assert ctx.completed_sessions == 1
        assert "Decorators" in ctx.strong_topics
        assert "Closure scope" in ctx.weak_topics
