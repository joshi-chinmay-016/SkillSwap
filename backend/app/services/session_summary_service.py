import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.learning_session_repository import get_session as repo_get_session
from app.repositories.session_summary_repository import (
    create_summary as repo_create_summary,
    get_session_summary as repo_get_session_summary,
    update_summary as repo_update_summary,
    delete_summary as repo_delete_summary,
)
from app.schemas.session_summary import (
    SessionSummaryCreate,
    SessionSummaryCreateResponse,
    SessionSummaryResponse,
    SessionSummaryUpdate,
)

logger = logging.getLogger(__name__)


def _resolve_session(db: Session, session_id: int, user_id: int):
    """
    Internal helper — fetch session, verify existence and ownership.
    Raises HTTPException on any failure.
    """
    session = repo_get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning session not found"
        )
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this session's summary"
        )
    return session


def create_summary(
    db: Session,
    session_id: int,
    user_id: int,
    data: SessionSummaryCreate
) -> SessionSummaryCreateResponse:
    """
    Create a SessionSummary for a completed, user-owned session.

    Business rules enforced:
    - Session must exist
    - Session must belong to the authenticated user
    - Session must be COMPLETED (not ACTIVE or ARCHIVED)
    - Summary must not already exist (no duplicates)
    """
    session = _resolve_session(db, session_id, user_id)

    # Reject sessions that are not yet completed
    if session.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A summary can only be created for a COMPLETED session. "
                f"Current status: {session.status}"
            )
        )

    # Prevent duplicate summaries
    existing = repo_get_session_summary(db, session_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A summary already exists for this session"
        )

    try:
        summary = repo_create_summary(db, session_id, data)
        db.commit()
        db.refresh(summary)

        logger.info(
            f"Session summary created: summary_id={summary.id}, "
            f"session_id={session_id}, user_id={user_id}"
        )

        # Auto-rebuild the AI learning profile after summary creation
        _trigger_profile_rebuild(db, user_id)

        return SessionSummaryCreateResponse(
            summary_id=summary.id,
            uuid=summary.uuid,
            session_id=summary.session_id,
            created_at=summary.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Failed to create session summary: session_id={session_id}, "
            f"user_id={user_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session summary: {str(e)}"
        )


def create_summary_internal(
    db: Session,
    session_id: int,
    data: SessionSummaryCreate
) -> None:
    """
    Internal helper used by the AI pipeline during session completion.

    Unlike `create_summary`, this:
    - Does NOT validate ownership (already validated upstream)
    - Does NOT commit (caller owns the transaction)
    - Does NOT raise HTTPException (caller handles errors silently)
    - Silently skips if a summary already exists
    """
    existing = repo_get_session_summary(db, session_id)
    if existing:
        logger.info(
            f"Summary already exists for session_id={session_id}, skipping AI generation."
        )
        return

    summary = repo_create_summary(db, session_id, data)
    logger.info(
        f"AI-generated session summary persisted: summary_id={summary.id}, "
        f"session_id={session_id}"
    )

    # Auto-rebuild the AI learning profile after AI-generated summary
    session = repo_get_session(db, session_id)
    if session:
        _trigger_profile_rebuild(db, session.user_id)


def get_summary(
    db: Session,
    session_id: int,
    user_id: int
) -> SessionSummaryResponse:
    """
    Retrieve the summary for a session.

    Validates ownership and returns full structured response.
    """
    _resolve_session(db, session_id, user_id)

    summary = repo_get_session_summary(db, session_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No summary found for this session"
        )

    return SessionSummaryResponse.model_validate(summary)


def update_summary(
    db: Session,
    session_id: int,
    user_id: int,
    data: SessionSummaryUpdate
) -> SessionSummaryResponse:
    """
    Update an existing session summary.

    Primarily used for AI regeneration. All fields are optional.
    Validates ownership before update.
    """
    _resolve_session(db, session_id, user_id)

    summary = repo_get_session_summary(db, session_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No summary found for this session"
        )

    try:
        updated = repo_update_summary(db, summary, data)
        db.commit()
        db.refresh(updated)

        logger.info(
            f"Session summary updated: summary_id={summary.id}, "
            f"session_id={session_id}, user_id={user_id}"
        )

        return SessionSummaryResponse.model_validate(updated)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Failed to update session summary: session_id={session_id}, "
            f"user_id={user_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session summary: {str(e)}"
        )


def delete_summary(
    db: Session,
    session_id: int,
    user_id: int
) -> None:
    """
    Delete the summary for a session.

    Validates ownership before deletion. Hard delete — no soft delete.
    """
    _resolve_session(db, session_id, user_id)

    summary = repo_get_session_summary(db, session_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No summary found for this session"
        )

    try:
        repo_delete_summary(db, summary)
        db.commit()

        logger.info(
            f"Session summary deleted: session_id={session_id}, user_id={user_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Failed to delete session summary: session_id={session_id}, "
            f"user_id={user_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session summary: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Auto-rebuild trigger
# ---------------------------------------------------------------------------

def _trigger_profile_rebuild(db: Session, user_id: int) -> None:
    """
    Fire-and-forget AI profile rebuild after summary creation.
    Never raises — failures are logged as warnings only.
    """
    try:
        from app.services.ai_context_service import rebuild_user_ai_context
        rebuild_user_ai_context(db, user_id)
        logger.info(
            "AI learning profile auto-rebuilt after summary creation: "
            "user_id=%d", user_id
        )
    except Exception as exc:
        logger.warning(
            "AI profile auto-rebuild failed (non-blocking) for "
            "user_id=%d: %s", user_id, str(exc)
        )
