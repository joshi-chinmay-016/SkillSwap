from app.ai.services.llm_service import (
    LLMService
)

from app.ai.services.roadmap_service import (
    RoadmapService
)

from app.ai.services.skill_gap_service import (
    SkillGapService
)

_llm_service = LLMService()

_roadmap_service = RoadmapService()

_skill_gap_service = SkillGapService()


def get_llm_service():

    return _llm_service


def get_roadmap_service():

    return _roadmap_service


def get_skill_gap_service():

    return _skill_gap_service