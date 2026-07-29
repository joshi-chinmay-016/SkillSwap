import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.schemas.session_summary import (
    SessionSummaryCreate,
    SessionSummaryCreateResponse,
    SessionSummaryResponse,
    SessionSummaryUpdate,
)
from app.services import session_summary_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sessions",
    tags=["Session Summaries"]
)


@router.post(
    "/{session_id}/summary",
    response_model=SessionSummaryCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Session Summary",
    description=(
        "Create a structured AI-ready summary for a completed learning session. "
        "The session must be COMPLETED and must not already have a summary."
    ),
    responses={
        201: {
            "description": "Summary created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "summary_id": 1,
                        "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "session_id": 42,
                        "created_at": "2026-07-29T10:00:00Z"
                    }
                }
            }
        },
        403: {"description": "Session belongs to another user"},
        404: {"description": "Session not found"},
        409: {"description": "Session is not COMPLETED, or summary already exists"},
    }
)
def create_session_summary(
    session_id: int,
    data: SessionSummaryCreate,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a structured summary for a completed learning session."""
    return session_summary_service.create_summary(
        db, session_id, current_user.id, data
    )


@router.get(
    "/{session_id}/summary",
    response_model=SessionSummaryResponse,
    summary="Get Session Summary",
    description="Retrieve the full structured summary for a learning session.",
    responses={
        200: {
            "description": "Summary retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "session_id": 42,
                        "summary": "The learner successfully explained Binary Search.",
                        "key_takeaways": [
                            "Binary Search",
                            "Divide and Conquer",
                            "O(log n)"
                        ],
                        "strengths": [
                            "Good explanation",
                            "Correct complexity analysis"
                        ],
                        "weaknesses": [
                            "Forgot edge cases"
                        ],
                        "follow_up_topics": [
                            "Lower Bound",
                            "Upper Bound"
                        ],
                        "created_at": "2026-07-29T10:00:00Z",
                        "updated_at": "2026-07-29T10:00:00Z"
                    }
                }
            }
        },
        403: {"description": "Session belongs to another user"},
        404: {"description": "Session or summary not found"},
    }
)
def get_session_summary(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Retrieve the structured summary for a learning session."""
    return session_summary_service.get_summary(
        db, session_id, current_user.id
    )


@router.put(
    "/{session_id}/summary",
    response_model=SessionSummaryResponse,
    summary="Update Session Summary",
    description=(
        "Update fields of an existing session summary. All fields are optional. "
        "Primarily used for future AI regeneration workflows."
    ),
    responses={
        200: {"description": "Summary updated successfully"},
        403: {"description": "Session belongs to another user"},
        404: {"description": "Session or summary not found"},
    }
)
def update_session_summary(
    session_id: int,
    data: SessionSummaryUpdate,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update an existing session summary."""
    return session_summary_service.update_summary(
        db, session_id, current_user.id, data
    )


@router.delete(
    "/{session_id}/summary",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Session Summary",
    description="Permanently delete a session summary. Hard delete — no soft delete.",
    responses={
        204: {"description": "Summary deleted successfully"},
        403: {"description": "Session belongs to another user"},
        404: {"description": "Session or summary not found"},
    }
)
def delete_session_summary(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Delete a session summary."""
    session_summary_service.delete_summary(
        db, session_id, current_user.id
    )


@router.post(
    "/{session_id}/summary/regenerate",
    response_model=SessionSummaryCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Regenerate Session Summary",
    description=(
        "Regenerate the AI summary for a completed session. "
        "Deletes the existing summary, generates a new one using the AI pipeline, "
        "and persists it. Useful after prompt improvements."
    ),
    responses={
        201: {"description": "Summary regenerated successfully"},
        403: {"description": "Session belongs to another user"},
        404: {"description": "Session not found"},
        409: {"description": "Session is not COMPLETED"},
        503: {"description": "AI generation failed"},
    }
)
def regenerate_session_summary(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Regenerate the AI-powered summary for a completed session.

    Workflow:
    1. Validate ownership and COMPLETED status
    2. Delete existing summary (if any)
    3. Generate new AI summary
    4. Persist and return
    """
    from app.services.session_summary_service import _resolve_session
    from app.repositories.session_summary_repository import (
        get_session_summary as repo_get_session_summary,
        delete_summary as repo_delete_summary,
        create_summary as repo_create_summary,
    )
    from app.ai.services.ai_session_summary_generator import AISessionSummaryGenerator
    from app.ai.schemas.session_summary import SessionSummaryContext
    from fastapi import HTTPException

    # 1. Validate session
    session = _resolve_session(db, session_id, current_user.id)

    if session.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Summary regeneration requires a COMPLETED session. "
                f"Current status: {session.status}"
            )
        )

    # 2. Delete existing summary
    existing = repo_get_session_summary(db, session_id)
    if existing:
        repo_delete_summary(db, existing)
        logger.info(
            f"Old summary deleted for regeneration: session_id={session_id}, "
            f"user_id={current_user.id}"
        )

    # 3. Generate new AI summary
    try:
        context = SessionSummaryContext(
            session_title=session.title,
            session_id=session_id,
        )
        generator = AISessionSummaryGenerator()
        new_data = generator.generate(context)

        logger.info(
            f"AI summary regenerated for session_id={session_id}"
        )
    except Exception as e:
        db.rollback()
        logger.error(
            f"AI regeneration failed for session_id={session_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI summary generation failed: {str(e)}"
        )

    # 4. Persist and return
    try:
        summary = repo_create_summary(db, session_id, new_data)
        db.commit()
        db.refresh(summary)

        logger.info(
            f"Regenerated summary persisted: summary_id={summary.id}, "
            f"session_id={session_id}"
        )

        return SessionSummaryCreateResponse(
            summary_id=summary.id,
            uuid=summary.uuid,
            session_id=summary.session_id,
            created_at=summary.created_at,
        )

    except Exception as e:
        db.rollback()
        logger.error(
            f"Failed to persist regenerated summary: session_id={session_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store regenerated summary: {str(e)}"
        )
