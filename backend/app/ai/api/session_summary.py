from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from app.ai.schemas.session_summary import (
    SessionSummaryRequest,
    SessionSummaryResponse
)

from app.ai.services.session_summary_service import (
    SessionSummaryService
)

from app.ai.dependencies import (
    get_session_summary_service
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.post(
    "/session-summary",
    response_model=SessionSummaryResponse
)
def summarize_session(

    request: SessionSummaryRequest,

    session_summary_service: SessionSummaryService = Depends(
        get_session_summary_service
    )

):

    try:

        return session_summary_service.summarize(
            request
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Failed to generate session summary."
        )