"""
Unit and integration tests for Day 64 Part A2 — Internal Tool Execution Framework.
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from app.ai.models.mentor_intent import MentorIntent, IntentResult
from app.ai.tools.mentor_tool import MentorTool, ToolResult, ToolValidationError
from app.ai.tools.tool_registry import ToolRegistry
from app.ai.tools.tool_dispatcher import ToolDispatcher
from app.ai.tools.learning_progress_tool import LearningProgressTool
from app.ai.tools.journey_tool import JourneyTool
from app.ai.tools.session_summary_tool import SessionSummaryTool
from app.ai.tools.ai_context_tool import AIContextTool
from app.ai.tools.learning_analytics_tool import LearningAnalyticsTool
from app.ai.prompts.mentor_prompt_builder import MentorPromptBuilder
from app.ai.schemas.mentor import PersonalizationMeta
from app.ai.services.ai_mentor_service import AIMentorService
from app.models.ai_context import AIContext


class DummyTool(MentorTool):

    @property
    def name(self) -> str:
        return "DummyTool"

    @property
    def description(self) -> str:
        return "Test tool"

    @property
    def supported_intents(self):
        return [MentorIntent.LEARNING_PROGRESS]

    def _execute(self, db, user_id, parameters):
        return {"test_key": "test_value"}


class TestToolRegistryAndDispatcher:

    def test_tool_registry_registration_and_resolution(self):
        registry = ToolRegistry()
        tool = DummyTool()
        registry.register(tool)

        resolved = registry.resolve(MentorIntent.LEARNING_PROGRESS)
        assert resolved is tool

        none_resolved = registry.resolve(MentorIntent.GENERAL_CHAT)
        assert none_resolved is None

        assert "DummyTool" in registry.list_tools()

    def test_tool_dispatcher_success(self):
        registry = ToolRegistry()
        registry.register(DummyTool())
        dispatcher = ToolDispatcher(registry=registry)

        intent_res = IntentResult(
            intent=MentorIntent.LEARNING_PROGRESS,
            confidence=0.9,
            reason="Match",
        )

        res = dispatcher.dispatch(db=None, user_id=1, intent_result=intent_res)
        assert res is not None
        assert res.success is True
        assert res.tool == "DummyTool"
        assert res.data == {"test_key": "test_value"}

        metrics = dispatcher.get_metrics()
        assert metrics["total_dispatches"] == 1
        assert metrics["success_count"] == 1

    def test_tool_dispatcher_no_tool_registered(self):
        registry = ToolRegistry()
        dispatcher = ToolDispatcher(registry=registry)

        intent_res = IntentResult(
            intent=MentorIntent.GENERAL_CHAT,
            confidence=0.9,
            reason="Greeting",
        )

        res = dispatcher.dispatch(db=None, user_id=1, intent_result=intent_res)
        assert res is None

    def test_tool_validation_failure(self):
        tool = DummyTool()
        res = tool.execute(db=None, user_id=0)
        assert res.success is False
        assert "Validation error" in res.error


class TestConcreteTools:

    @patch("app.services.journey_service.get_my_journeys")
    @patch("app.services.learning_activity_service.get_user_learning_streak")
    @patch("app.services.ai_context_service.get_user_ai_context")
    def test_learning_progress_tool(self, mock_ctx, mock_streak, mock_journeys):
        mock_journeys.return_value = []
        mock_streak.return_value = MagicMock(current_streak=5, longest_streak=10, last_active_date="2026-08-01")
        mock_ctx.return_value = MagicMock(completed_sessions=12)

        tool = LearningProgressTool()
        res = tool.execute(db=None, user_id=1)

        assert res.success is True
        assert res.data["completed_sessions"] == 12
        assert res.data["current_streak"] == 5

    @patch("app.services.ai_context_service.get_user_ai_context")
    def test_ai_context_tool(self, mock_ctx):
        mock_ctx.return_value = MagicMock(
            strong_topics=["Arrays", "Python"],
            weak_topics=["Graphs"],
            learning_interests=["AI"],
            learning_style="Visual",
            recommended_topics=["DP"],
            completed_sessions=15,
            overall_summary="Doing great",
        )

        tool = AIContextTool()
        res = tool.execute(db=None, user_id=1)

        assert res.success is True
        assert res.data["has_profile"] is True
        assert res.data["strong_topics"] == ["Arrays", "Python"]
        assert res.data["weak_topics"] == ["Graphs"]


class TestPromptBuilderWithTools:

    def test_prompt_builder_injects_platform_data(self):
        builder = MentorPromptBuilder()
        meta = PersonalizationMeta(difficulty_level="Intermediate")
        tool_res = ToolResult(
            tool="LearningProgressTool",
            success=True,
            data={"completed_sessions": 15, "current_streak": 3},
        )

        prompt = builder.build(
            question="What is my progress?",
            context=None,
            meta=meta,
            tool_results=[tool_res],
        )

        assert "[Platform Data — Retrieved from SkillSwap]" in prompt
        assert "LearningProgressTool" in prompt
        assert '"completed_sessions": 15' in prompt


class TestAIMentorServiceIntegration:

    @patch("app.ai.services.ai_mentor_service.get_user_ai_context")
    def test_ai_mentor_service_with_intent_and_tool(self, mock_ctx):
        mock_ctx.return_value = None

        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({
            "response": "Based on platform data, you have completed 15 sessions and have a streak of 3 days.",
            "recommended_topics": ["Tree Traversal"],
            "difficulty_level": "Intermediate",
        })

        registry = ToolRegistry()
        tool = DummyTool()
        registry.register(tool)
        dispatcher = ToolDispatcher(registry=registry)

        mentor = AIMentorService(
            llm_service=mock_llm,
            dispatcher=dispatcher,
        )

        db_mock = MagicMock()
        response = mentor.chat(db=db_mock, user_id=1, question="How many sessions completed in my learning progress?")

        assert response.response is not None
        assert len(response.response) > 20
        mock_llm.generate.assert_called_once()
        prompt_arg = mock_llm.generate.call_args[1]["prompt"]
        assert "[Platform Data — Retrieved from SkillSwap]" in prompt_arg
