from app.core.config import settings
from app.ai.services import (
    LLMService,
    RoadmapService,
    SkillGapService,
    SessionSummaryService,
    MentorRecommendationService,
    AIMentorService,
    IntentClassificationService,
)
from app.ai.tools import (
    ToolRegistry,
    ToolDispatcher,
    LearningProgressTool,
    JourneyTool,
    SessionSummaryTool,
    AIContextTool,
    LearningAnalyticsTool,
)

_llm_service = LLMService()

_roadmap_service = RoadmapService()

_skill_gap_service = SkillGapService()

_session_summary_service = SessionSummaryService()

_mentor_recommendation_service = MentorRecommendationService()

_intent_classification_service = IntentClassificationService()

_tool_registry = ToolRegistry()
_tool_registry.register(LearningProgressTool())
_tool_registry.register(JourneyTool())
_tool_registry.register(SessionSummaryTool())
_tool_registry.register(AIContextTool())
_tool_registry.register(LearningAnalyticsTool())

_tool_dispatcher = ToolDispatcher(
    registry=_tool_registry,
    timeout_seconds=getattr(settings, "MENTOR_TOOL_TIMEOUT_SECONDS", 5),
)

_ai_mentor_service = AIMentorService(
    llm_service=_llm_service,
    intent_service=_intent_classification_service,
    dispatcher=_tool_dispatcher,
)


def get_llm_service():
    return _llm_service


def get_roadmap_service():
    return _roadmap_service


def get_skill_gap_service():
    return _skill_gap_service


def get_session_summary_service():
    return _session_summary_service


def get_mentor_recommendation_service():
    return _mentor_recommendation_service


def get_intent_classification_service():
    return _intent_classification_service


def get_tool_registry():
    return _tool_registry


def get_tool_dispatcher():
    return _tool_dispatcher


def get_ai_mentor_service():
    return _ai_mentor_service