"""
Unit and Integration tests for Day 62 Context-Aware AI Mentor.
Tests:
- MentorIntelligenceEngine (weak/strong topics, difficulty inference, learning style, recommendation ranking)
- MentorPromptBuilder (prompt composition, context injection, mode headers)
- AIMentorService (LLM interaction, JSON validation, retry logic, plain-text fallback)
- API endpoints (POST /mentor/chat, GET /mentor/health, authentication)
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.ai_context import AIContext
from app.ai.schemas.mentor import MentorChatRequest, MentorChatResponse, PersonalizationMeta
from app.ai.services.mentor_intelligence_engine import MentorIntelligenceEngine
from app.ai.prompts.mentor_prompt_builder import MentorPromptBuilder
from app.ai.services.ai_mentor_service import AIMentorService


# ============================================================================
# 1. MentorIntelligenceEngine Unit Tests
# ============================================================================

class TestMentorIntelligenceEngine:

    def setup_method(self):
        self.engine = MentorIntelligenceEngine()

    def test_generic_fallback_when_context_is_none(self):
        meta = self.engine.analyze(context=None, question="Explain binary search")
        assert meta.difficulty_level == "Intermediate"
        assert meta.use_analogies is True
        assert meta.topic_is_weak is False
        assert meta.topic_is_strong is False
        assert meta.recommended_topics == []

    def test_weak_topic_detection_and_difficulty(self):
        context = AIContext(
            user_id=1,
            completed_sessions=3,
            weak_topics=["Graphs", "Dynamic Programming"],
            strong_topics=["Arrays"],
        )
        meta = self.engine.analyze(context=context, question="How do I solve a Graphs problem?")
        assert meta.topic_is_weak is True
        assert meta.topic_is_strong is False
        assert meta.difficulty_level == "Beginner"
        assert meta.use_analogies is True
        assert meta.build_prerequisites is True

    def test_strong_topic_detection_and_difficulty(self):
        context = AIContext(
            user_id=1,
            completed_sessions=25,
            weak_topics=["Graphs"],
            strong_topics=["Arrays", "Binary Search"],
        )
        meta = self.engine.analyze(context=context, question="Explain Binary Search optimizations")
        assert meta.topic_is_strong is True
        assert meta.topic_is_weak is False
        assert meta.difficulty_level == "Advanced"
        assert meta.skip_basics is True

    def test_learning_style_parsing(self):
        context_coding = AIContext(user_id=1, learning_style="Prefers code exercises and implementation-first approach")
        meta_coding = self.engine.analyze(context=context_coding, question="Explain Hashing")
        assert "implementation-first" in meta_coding.style_instruction

        context_theory = AIContext(user_id=1, learning_style="Prefers concept explanation and theory first")
        meta_theory = self.engine.analyze(context=context_theory, question="Explain Hashing")
        assert "concept-first" in meta_theory.style_instruction

    def test_recommendations_selection(self):
        context = AIContext(
            user_id=1,
            recommended_topics=["Graph Traversal", "Dijkstra", "Trie Data Structure", "Segment Tree"],
        )
        meta = self.engine.analyze(context=context, question="Tell me about Graph algorithms")
        # Should prioritize topics matching 'Graph'
        assert len(meta.recommended_topics) <= 4
        assert "Graph Traversal" in meta.recommended_topics


# ============================================================================
# 2. MentorPromptBuilder Unit Tests
# ============================================================================

class TestMentorPromptBuilder:

    def setup_method(self):
        self.builder = MentorPromptBuilder()
        self.engine = MentorIntelligenceEngine()

    def test_build_prompt_with_context(self):
        context = AIContext(
            user_id=1,
            completed_sessions=10,
            overall_summary="Learner has mastered basic data structures.",
            strong_topics=["Arrays", "Strings"],
            weak_topics=["Trees"],
            learning_interests=["Algorithms"],
            recommended_topics=["Binary Trees", "AVL Trees"],
            learning_style="Visual learner",
        )
        meta = self.engine.analyze(context, question="Explain Tree Traversal")
        prompt = self.builder.build(question="Explain Tree Traversal", context=context, meta=meta)

        assert "[Mentor Mode: Teaching]" in prompt
        assert "[Learner Profile]" in prompt
        assert "Strong Topics" in prompt
        assert "Arrays, Strings" in prompt
        assert "Areas for Improvement" in prompt
        assert "Trees" in prompt
        assert "[Learner Question]" in prompt
        assert "Explain Tree Traversal" in prompt

    def test_build_prompt_without_context(self):
        meta = self.engine.analyze(context=None, question="What is recursion?")
        prompt = self.builder.build(question="What is recursion?", context=None, meta=meta)

        assert "[Mentor Mode: Teaching]" in prompt
        assert "No persistent profile available" in prompt
        assert "What is recursion?" in prompt


# ============================================================================
# 3. AIMentorService Unit Tests
# ============================================================================

class TestAIMentorService:

    def test_chat_success_structured_response(self):
        mock_llm = MagicMock()
        valid_json_response = json.dumps({
            "response": "Binary search is an efficient algorithm for searching a sorted array by repeatedly dividing the search interval in half.",
            "recommended_topics": ["Lower Bound", "Upper Bound"],
            "difficulty_level": "Intermediate"
        })
        mock_llm.generate.return_value = valid_json_response

        service = AIMentorService(llm_service=mock_llm)
        db_mock = MagicMock()

        with patch("app.ai.services.ai_mentor_service.get_user_ai_context", return_value=None):
            result = service.chat(db=db_mock, user_id=1, question="Explain Binary Search")

        assert isinstance(result, MentorChatResponse)
        assert "Binary search is an efficient algorithm" in result.response
        assert result.recommended_topics == ["Lower Bound", "Upper Bound"]
        assert result.difficulty_level == "Intermediate"

    def test_chat_retry_on_invalid_json(self):
        mock_llm = MagicMock()
        invalid_first_response = "Here is an explanation: Binary search is great."
        valid_second_response = json.dumps({
            "response": "Binary search divides the search space in half each step, achieving logarithmic O(log N) time complexity.",
            "recommended_topics": ["Trie"],
            "difficulty_level": "Intermediate"
        })
        mock_llm.generate.side_effect = [invalid_first_response, valid_second_response]

        service = AIMentorService(llm_service=mock_llm)
        db_mock = MagicMock()

        with patch("app.ai.services.ai_mentor_service.get_user_ai_context", return_value=None):
            result = service.chat(db=db_mock, user_id=1, question="Explain Binary Search")

        assert mock_llm.generate.call_count == 2
        assert "Binary search divides the search space" in result.response

    def test_chat_fallback_to_plain_text(self):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Binary search works by taking the middle element and comparing it to the target value iteratively."

        service = AIMentorService(llm_service=mock_llm)
        db_mock = MagicMock()

        with patch("app.ai.services.ai_mentor_service.get_user_ai_context", return_value=None):
            result = service.chat(db=db_mock, user_id=1, question="Explain Binary Search")

        assert isinstance(result, MentorChatResponse)
        assert "Binary search works by taking" in result.response


# ============================================================================
# 4. API Integration Tests
# ============================================================================

class TestAIMentorAPI:

    def setup_method(self):
        self.client = TestClient(app)

    def test_mentor_health_endpoint(self):
        res = self.client.get("/mentor/health")
        assert res.status_code == 200
        assert res.json() == {"status": "healthy"}

    def test_mentor_chat_unauthenticated(self):
        res = self.client.post("/mentor/chat", json={"message": "Explain recursion"})
        assert res.status_code == 401

    def test_mentor_chat_authenticated(self):
        from app.dependencies.current_user import get_current_user

        mock_user = MagicMock()
        mock_user.id = 42

        mock_service = MagicMock()
        mock_service.chat.return_value = MentorChatResponse(
            response="Recursion is a technique where a function calls itself.",
            recommended_topics=["Base Cases", "Tail Recursion"],
            difficulty_level="Beginner"
        )

        from app.ai.dependencies import get_ai_mentor_service

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_ai_mentor_service] = lambda: mock_service

        try:
            res = self.client.post("/mentor/chat", json={"message": "Explain recursion"})
            assert res.status_code == 200
            data = res.json()
            assert "Recursion is a technique" in data["response"]
            assert data["recommended_topics"] == ["Base Cases", "Tail Recursion"]
            assert data["difficulty_level"] == "Beginner"
        finally:
            app.dependency_overrides.clear()
