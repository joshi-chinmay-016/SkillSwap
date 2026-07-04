from app.ai.services.llm_service import (
    LLMService
)

from app.ai.schemas.session_summary import (
    SessionSummaryRequest,
    SessionSummaryResponse
)

from app.ai.prompts.session_summary_prompt import (
    build_session_summary_prompt
)

from app.ai.prompts.system_prompts import (
    SUMMARY_SYSTEM_PROMPT
)

from app.ai.utils import (
    parse_json_response
)


class SessionSummaryService:

    def __init__(self):

        self.llm = LLMService()

    def summarize(

        self,

        request: SessionSummaryRequest

    ) -> SessionSummaryResponse:

        prompt = build_session_summary_prompt(
            request
        )

        response = self.llm.generate(

            prompt=prompt,

            system_prompt=SUMMARY_SYSTEM_PROMPT

        )

        data = parse_json_response(
            response
        )

        return SessionSummaryResponse(
            **data
        )