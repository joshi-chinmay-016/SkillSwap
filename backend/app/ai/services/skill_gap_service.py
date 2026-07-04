from app.ai.services.llm_service import (
    LLMService
)

from app.ai.schemas.skill_gap import (
    SkillGapRequest,
    SkillGapResponse
)

from app.ai.prompts.skill_gap_prompt import (
    build_skill_gap_prompt
)

from app.ai.utils import (
    parse_json_response
)


class SkillGapService:

    def __init__(self):

        self.llm = LLMService()

    def analyze(

        self,

        request: SkillGapRequest

    ) -> SkillGapResponse:

        prompt = build_skill_gap_prompt(
            request
        )

        response = self.llm.generate(
            prompt=prompt
        )

        data = parse_json_response(
            response
        )

        return SkillGapResponse(
            **data
        )