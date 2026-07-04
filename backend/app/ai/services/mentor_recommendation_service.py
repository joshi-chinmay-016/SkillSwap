from sqlalchemy.orm import Session

from app.services.mentor_service import (
    discover_mentors
)

from app.ai.services import (
    LLMService
)

from app.ai.schemas.mentor_recommendation import (
    MentorRecommendationRequest,
    MentorRecommendationResponse
)

from app.ai.prompts import (
    build_mentor_recommendation_prompt,
    MENTOR_RECOMMENDATION_SYSTEM_PROMPT
)

from app.ai.utils import (
    parse_json_response
)


class MentorRecommendationService:

    def __init__(self):

        self.llm = LLMService()

    def recommend(

    self,

    db: Session,

    request: MentorRecommendationRequest

    ) -> MentorRecommendationResponse:

        mentors = discover_mentors(

        db,

        skill=request.target_skill,

        page=1,

        size=5

    )

        if not mentors:

            return MentorRecommendationResponse(
                mentors=[]
        )

        prompt = build_mentor_recommendation_prompt(

        request,

        mentors

    )

        response = self.llm.generate(

        prompt=prompt,

        system_prompt=MENTOR_RECOMMENDATION_SYSTEM_PROMPT

    )

        data = parse_json_response(
        response
    )

        return MentorRecommendationResponse(
        **data
    )   