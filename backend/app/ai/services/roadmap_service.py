import json

from app.ai.services.llm_service import LLMService

from app.ai.schemas.roadmap import (
    RoadmapRequest,
    RoadmapResponse
)

from app.ai.prompts.roadmap_prompt import (
    build_roadmap_prompt
)

from app.ai.prompts.system_prompts import (
    ROADMAP_SYSTEM_PROMPT
)
from app.ai.utils.json_parser import (
    parse_json_response
)


class RoadmapService:

    def __init__(self):

        self.llm = LLMService()

    def generate_roadmap(

        self,

        request: RoadmapRequest

    ) -> RoadmapResponse:

        prompt = build_roadmap_prompt(
            request
        )

        response = self.llm.generate(

            prompt=prompt,

            system_prompt=ROADMAP_SYSTEM_PROMPT

        )

        roadmap = parse_json_response(
        response
        )

        return RoadmapResponse(
            **roadmap
        )