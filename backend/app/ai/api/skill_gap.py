from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from app.ai.schemas.skill_gap import (
    SkillGapRequest,
    SkillGapResponse
)

from app.ai.services.skill_gap_service import (
    SkillGapService
)

from app.ai.dependencies import (
    get_skill_gap_service
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.post(
    "/skill-gap",
    response_model=SkillGapResponse
)
def analyze_skill_gap(

    request: SkillGapRequest,

    skill_gap_service: SkillGapService = Depends(
        get_skill_gap_service
    )

):

    try:

        return skill_gap_service.analyze(
            request
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Failed to analyze skill gap."
        )