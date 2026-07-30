import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.ai.schemas.mentor import MentorChatRequest, MentorChatResponse
from app.ai.services.ai_mentor_service import AIMentorService
from app.ai.dependencies import get_ai_mentor_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/mentor",
    tags=["AI Mentor"]
)


@router.get(
    "/health",
    summary="AI Mentor health check",
)
def mentor_health():
    """
    Health check endpoint for deployment and monitoring.
    Returns healthy status without requiring authentication.
    """
    return {"status": "healthy"}


@router.post(
    "/chat",
    response_model=MentorChatResponse,
    summary="Chat with the AI Learning Mentor",
)
def mentor_chat(
    request: MentorChatRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    mentor_service: AIMentorService = Depends(get_ai_mentor_service),
):
    """
    Send a message to the Context-Aware AI Learning Mentor.

    The mentor adapts its response based on the learner's persistent AI Profile:
    - Adjusts explanation depth (Beginner / Intermediate / Advanced)
    - Detects knowledge gaps and builds prerequisites
    - Skips basics for mastered topics
    - Recommends logically next topics

    Requires authentication. Users access only their own AI Context.
    """
    logger.info(
        "POST /mentor/chat — user_id=%d message_len=%d",
        current_user.id,
        len(request.message),
    )

    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message cannot be empty.",
        )

    try:
        result = mentor_service.chat(
            db=db,
            user_id=current_user.id,
            question=request.message,
        )
        return result

    except HTTPException:
        raise

    except TimeoutError:
        logger.error("POST /mentor/chat — LLM timeout for user_id=%d", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The AI Mentor took too long to respond. Please try again.",
        )

    except Exception as exc:
        logger.error(
            "POST /mentor/chat — unexpected error for user_id=%d: %s",
            current_user.id,
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate a mentor response. Please try again.",
        )
