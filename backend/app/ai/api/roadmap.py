from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from app.ai.schemas.roadmap import (
    RoadmapRequest,
    RoadmapResponse
)

from app.ai.services.roadmap_service import (
    RoadmapService
)

from app.ai.dependencies import (
    get_roadmap_service
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.post(
    "/roadmap",
    response_model=RoadmapResponse
)
def generate_roadmap(

    request: RoadmapRequest,

    roadmap_service: RoadmapService = Depends(
        get_roadmap_service
    )

):

    try:

        return roadmap_service.generate_roadmap(
            request
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Failed to generate roadmap."
        )