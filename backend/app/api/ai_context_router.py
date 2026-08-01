"""
AI Context Router — Learning AI Profile endpoints.

Provides:
  GET    /users/me/context              — Retrieve the user's AI learning profile
  POST   /users/me/context/regenerate   — Rebuild profile from all session data
  PATCH  /users/me/context              — Update user-editable profile fields
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.schemas.ai_context import AIContextResponse, AIContextUpdate
from app.services.ai_context_service import (
    get_user_ai_context,
    rebuild_user_ai_context,
    update_user_ai_context,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users/me/context",
    tags=["AI Profile"],
)


@router.get(
    "",
    response_model=AIContextResponse,
    summary="Get AI Learning Profile",
    description=(
        "Retrieve the authenticated user's persistent AI learning profile. "
        "Returns 404 if no profile exists yet — the user should complete "
        "a session and create a summary first, or call /regenerate."
    ),
    responses={
        200: {"description": "AI profile retrieved successfully"},
        404: {"description": "No AI profile found for this user"},
    },
)
def get_ai_context(
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return the user's persistent AI learning profile."""
    context = get_user_ai_context(db, current_user.id)

    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No AI learning profile found. Complete a session and create a summary to build your profile.",
        )

    return AIContextResponse.model_validate(context)


@router.post(
    "/regenerate",
    response_model=AIContextResponse,
    summary="Regenerate AI Learning Profile",
    description=(
        "Rebuild the user's AI learning profile from scratch by aggregating "
        "all completed session summaries, learning journeys, and activity data. "
        "Creates the profile if it doesn't exist yet."
    ),
    responses={
        200: {"description": "Profile regenerated successfully"},
        500: {"description": "Profile regeneration failed"},
    },
)
def regenerate_ai_context(
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Rebuild the AI learning profile from all available data."""
    try:
        context = rebuild_user_ai_context(db, current_user.id)

        if not context:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to rebuild AI learning profile.",
            )

        db.commit()
        db.refresh(context)

        logger.info(
            "AI profile regenerated via API: user_id=%d, version=%d",
            current_user.id,
            context.context_version,
        )

        return AIContextResponse.model_validate(context)

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.error(
            "AI profile regeneration failed for user_id=%d: %s",
            current_user.id,
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile regeneration failed: {str(exc)}",
        )


@router.patch(
    "",
    response_model=AIContextResponse,
    summary="Update AI Learning Profile",
    description=(
        "Update user-editable fields of the AI learning profile. "
        "Only learning_interests and learning_style can be manually changed. "
        "Data-driven fields (strong_topics, weak_topics, recommended_topics) "
        "can only be changed via /regenerate."
    ),
    responses={
        200: {"description": "Profile updated successfully"},
        404: {"description": "No AI profile found — regenerate first"},
    },
)
def update_ai_context(
    data: AIContextUpdate,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update user-editable profile fields."""
    try:
        context = update_user_ai_context(db, current_user.id, data)

        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No AI learning profile found. Use /regenerate to create one first.",
            )

        db.commit()
        db.refresh(context)

        logger.info(
            "AI profile updated via API: user_id=%d, version=%d",
            current_user.id,
            context.context_version,
        )

        return AIContextResponse.model_validate(context)

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.error(
            "AI profile update failed for user_id=%d: %s",
            current_user.id,
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(exc)}",
        )
