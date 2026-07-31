"""
Unit and Integration tests for Day 63 Persistent AI Mentor Conversations (Parts A1 & A2).
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.models.base import Base
from app.models.user import User
from app.models.mentor_conversation import MentorConversation, ConversationStatus
from app.models.mentor_message import MentorMessage, MessageRole
from app.ai.schemas.mentor import MentorChatResponse
from app.ai.dependencies import get_ai_mentor_service



# Setup SQLite in-memory DB for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    User.__table__.create(bind=engine, checkfirst=True)
    MentorConversation.__table__.create(bind=engine, checkfirst=True)
    MentorMessage.__table__.create(bind=engine, checkfirst=True)
    
    db = TestingSessionLocal()
    
    # Create test users
    user1 = User(id=1, email="test1@example.com", name="Test User 1", password_hash="hash")
    user2 = User(id=2, email="test2@example.com", name="Test User 2", password_hash="hash")
    db.add(user1)
    db.add(user2)
    db.commit()
    db.close()



    def override_get_db():
        try:
            db_session = TestingSessionLocal()
            yield db_session
        finally:
            db_session.close()

    def override_get_current_user():
        db_session = TestingSessionLocal()
        user = db_session.query(User).filter(User.id == 1).first()
        db_session.close()
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield

    app.dependency_overrides.clear()
    MentorMessage.__table__.drop(bind=engine, checkfirst=True)
    MentorConversation.__table__.drop(bind=engine, checkfirst=True)
    User.__table__.drop(bind=engine, checkfirst=True)



@pytest.fixture
def mock_ai_mentor_service():
    mock_service = MagicMock()
    mock_service.chat_in_conversation.return_value = MentorChatResponse(
        response="Graph algorithms explore nodes and edges systematically.",
        recommended_topics=["Breadth First Search", "Depth First Search"],
        difficulty_level="Beginner",
    )
    app.dependency_overrides[get_ai_mentor_service] = lambda: mock_service
    return mock_service


class TestMentorConversationsAPI:

    def test_create_conversation(self, mock_ai_mentor_service):
        client = TestClient(app)
        response = client.post("/mentor/conversations", json={"title": "Graph Algorithms"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Graph Algorithms"
        assert data["user_id"] == 1
        assert data["status"] == "ACTIVE"

    def test_list_conversations(self, mock_ai_mentor_service):
        client = TestClient(app)
        client.post("/mentor/conversations", json={"title": "Chat 1"})
        client.post("/mentor/conversations", json={"title": "Chat 2"})

        response = client.get("/mentor/conversations")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["conversations"]) == 2

    def test_get_conversation_details(self, mock_ai_mentor_service):
        client = TestClient(app)
        create_res = client.post("/mentor/conversations", json={"title": "Single Chat"})
        conv_id = create_res.json()["id"]

        get_res = client.get(f"/mentor/conversations/{conv_id}")
        assert get_res.status_code == 200
        assert get_res.json()["title"] == "Single Chat"

    def test_rename_conversation(self, mock_ai_mentor_service):
        client = TestClient(app)
        create_res = client.post("/mentor/conversations", json={"title": "Old Name"})
        conv_id = create_res.json()["id"]

        patch_res = client.patch(f"/mentor/conversations/{conv_id}", json={"title": "New Name"})
        assert patch_res.status_code == 200
        assert patch_res.json()["title"] == "New Name"

    def test_archive_conversation(self, mock_ai_mentor_service):
        client = TestClient(app)
        create_res = client.post("/mentor/conversations", json={"title": "To Archive"})
        conv_id = create_res.json()["id"]

        archive_res = client.patch(f"/mentor/conversations/{conv_id}/archive")
        assert archive_res.status_code == 200
        assert archive_res.json()["status"] == "ARCHIVED"

        # Attempting chat on archived conversation must fail
        chat_res = client.post(f"/mentor/conversations/{conv_id}/chat", json={"message": "Hello"})
        assert chat_res.status_code == 400

    def test_delete_conversation(self, mock_ai_mentor_service):
        client = TestClient(app)
        create_res = client.post("/mentor/conversations", json={"title": "To Delete"})
        conv_id = create_res.json()["id"]

        del_res = client.delete(f"/mentor/conversations/{conv_id}")
        assert del_res.status_code == 204

        get_res = client.get(f"/mentor/conversations/{conv_id}")
        assert get_res.status_code == 404

    def test_chat_in_conversation_flow(self, mock_ai_mentor_service):
        client = TestClient(app)
        create_res = client.post("/mentor/conversations", json={"title": "New Conversation"})
        conv_id = create_res.json()["id"]

        chat_res = client.post(
            f"/mentor/conversations/{conv_id}/chat",
            json={"message": "Explain graph algorithms"}
        )
        assert chat_res.status_code == 200
        data = chat_res.json()
        assert data["user_message"]["role"] == "USER"
        assert data["user_message"]["content"] == "Explain graph algorithms"
        assert data["assistant_message"]["role"] == "ASSISTANT"
        assert "Graph algorithms" in data["assistant_message"]["content"]
        assert len(data["recommended_topics"]) == 2

        # Verify auto-titling updated the title
        get_res = client.get(f"/mentor/conversations/{conv_id}")
        assert get_res.json()["title"] == "Explain graph algorithms"

        # Verify messages list endpoint
        msg_res = client.get(f"/mentor/conversations/{conv_id}/messages")
        assert msg_res.status_code == 200
        messages = msg_res.json()["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "USER"
        assert messages[1]["role"] == "ASSISTANT"

    def test_retry_mentor_message(self, mock_ai_mentor_service):
        client = TestClient(app)
        create_res = client.post("/mentor/conversations", json={"title": "Retry Chat"})
        conv_id = create_res.json()["id"]

        chat_res = client.post(
            f"/mentor/conversations/{conv_id}/chat",
            json={"message": "Why does BFS use a queue?"}
        )
        user_msg_id = chat_res.json()["user_message"]["id"]

        retry_res = client.post(f"/mentor/conversations/{conv_id}/messages/{user_msg_id}/retry")
        assert retry_res.status_code == 200
        retry_data = retry_res.json()
        assert retry_data["user_message"]["id"] == user_msg_id
        assert retry_data["assistant_message"]["role"] == "ASSISTANT"

    def test_unauthorized_conversation_access(self, mock_ai_mentor_service):
        client = TestClient(app)
        create_res = client.post("/mentor/conversations", json={"title": "User 1 Chat"})
        conv_id = create_res.json()["id"]

        # Override user to user 2
        def override_user2():
            db_session = TestingSessionLocal()
            user = db_session.query(User).filter(User.id == 2).first()
            db_session.close()
            return user

        app.dependency_overrides[get_current_user] = override_user2

        # User 2 tries to access User 1's conversation -> 403 Forbidden
        get_res = client.get(f"/mentor/conversations/{conv_id}")
        assert get_res.status_code == 403
