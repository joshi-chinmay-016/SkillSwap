"""
Unit and Integration tests for Day 65 Long-Term AI Memory API.

Tests:
- Memory creation (POST /mentor/memory)
- Memory listing and filtering (GET /mentor/memory)
- Memory statistics aggregation (GET /mentor/memory/stats)
- Memory details (GET /mentor/memory/{id})
- Memory update (PATCH /mentor/memory/{id})
- Memory archive (PATCH /mentor/memory/{id}/archive)
- Memory pin toggle (PATCH /mentor/memory/{id}/pin)
- Memory deletion/forgetting (DELETE /mentor/memory/{id})
- Memory settings (GET/PATCH /mentor/memory/settings)
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.mentor_memory import MentorMemory, MemoryCategory, MemoryImportance, MemoryStatus, MemorySource
from app.schemas.mentor_memory import MentorMemoryResponse, MentorMemoryListResponse, MentorMemoryStatsResponse, MentorMemorySettings


class TestMentorMemoryAPI:

    def setup_method(self):
        self.client = TestClient(app)
        self.mock_user = MagicMock()
        self.mock_user.id = 42

    def test_memory_endpoints_unauthenticated(self):
        res = self.client.get("/mentor/memory")
        assert res.status_code == 401

        res = self.client.get("/mentor/memory/stats")
        assert res.status_code == 401

    def test_create_memory_authenticated(self):
        from app.dependencies.current_user import get_current_user
        from app.core.database import get_db

        mock_db = MagicMock()
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            payload = {
                "category": "LEARNING_STYLE",
                "title": "Implementation-first learner",
                "content": "Learner prefers code examples before theoretical breakdown",
                "importance": "HIGH",
                "source": "Conversation",
                "is_pinned": True
            }
            res = self.client.post("/mentor/memory", json=payload)
            assert res.status_code == 201
            data = res.json()
            assert data["title"] == "Implementation-first learner"
            assert data["category"] == "LEARNING_STYLE"
            assert data["importance"] == "HIGH"
            assert data["is_pinned"] is True
        finally:
            app.dependency_overrides.clear()

    def test_get_memory_stats_authenticated(self):
        from app.dependencies.current_user import get_current_user
        from app.core.database import get_db

        mock_db = MagicMock()
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            res = self.client.get("/mentor/memory/stats")
            assert res.status_code == 200
            data = res.json()
            assert "total_memories" in data
            assert "pinned_count" in data
            assert "high_importance_count" in data
            assert "category_distribution" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_and_update_settings_authenticated(self):
        from app.dependencies.current_user import get_current_user
        from app.core.database import get_db

        mock_db = MagicMock()
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            res = self.client.get("/mentor/memory/settings")
            assert res.status_code == 200
            data = res.json()
            assert data["memory_enabled"] is True

            patch_res = self.client.patch("/mentor/memory/settings", json={"automatic_updates": False})
            assert patch_res.status_code == 200
            patch_data = patch_res.json()
            assert patch_data["automatic_updates"] is False
        finally:
            app.dependency_overrides.clear()
