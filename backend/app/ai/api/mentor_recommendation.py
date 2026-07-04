from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.core.database import (
    get_db
)

from app.ai.schemas.mentor_recommendation import (
    MentorRecommendationRequest,
    MentorRecommendationResponse
)

from app.ai.services import (
    MentorRecommendationService
)

from app.ai.dependencies import (
    get_mentor_recommendation_service
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.post(
    "/mentor-recommendation",
    response_model=MentorRecommendationResponse
)
def recommend_mentors(

    request: MentorRecommendationRequest,

    db: Session = Depends(get_db),

    recommendation_service: MentorRecommendationService = Depends(
        get_mentor_recommendation_service
    )

):

    try:

        return recommendation_service.recommend(
            db,
            request
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )