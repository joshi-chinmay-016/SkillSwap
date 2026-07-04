from app.ai.services import (
    LLMService,
    RoadmapService,
    SkillGapService,
    SessionSummaryService,
    MentorRecommendationService
)

_llm_service = LLMService()

_roadmap_service = RoadmapService()

_skill_gap_service = SkillGapService()

_session_summary_service = SessionSummaryService()

_mentor_recommendation_service = MentorRecommendationService()


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