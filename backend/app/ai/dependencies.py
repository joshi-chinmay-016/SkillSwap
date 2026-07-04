from app.ai.services.llm_service import (
    LLMService
)

from app.ai.services.roadmap_service import (
    RoadmapService
)

_llm_service = LLMService()

_roadmap_service = RoadmapService()


def get_llm_service():

    return _llm_service


def get_roadmap_service():

    return _roadmap_service