import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.learning_session_repository import (
    create_session as repo_create_session,
    get_session as repo_get_session,
    get_user_session as repo_get_user_session,
    get_journey_sessions as repo_get_journey_sessions,
    complete_session as repo_complete_session,
    archive_session as repo_archive_session,
)
from app.repositories.journey_repository import (
    get_learning_journey_by_id
)
from app.schemas.learning_session import (
    LearningSessionCreate,
    LearningSessionResponse,
    LearningSessionListResponse,
    LearningSessionCompleteResponse,
)

logger = logging.getLogger(__name__)


def create_session(
    db: Session,
    user_id: int,
    journey_id: int,
    session_data: LearningSessionCreate
) -> LearningSessionResponse:
    """
    Create a new learning session.
    Validates journey exists and is owned by the authenticated user.
    """
    # Validate journey exists
    journey = get_learning_journey_by_id(db, journey_id)
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning journey not found"
        )

    # Validate journey ownership
    if journey.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create sessions for this journey"
        )

    try:
        session = repo_create_session(
            db=db,
            user_id=user_id,
            journey_id=journey_id,
            title=session_data.title
        )
        db.commit()
        db.refresh(session)

        logger.info(
            f"Learning session created: session_id={session.id}, "
            f"uuid={session.uuid}, user_id={user_id}, journey_id={journey_id}"
        )

        return LearningSessionResponse.model_validate(session)

    except Exception as e:
        db.rollback()
        logger.error(
            f"Failed to create learning session for user_id={user_id}, "
            f"journey_id={journey_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create learning session: {str(e)}"
        )


def get_session(
    db: Session,
    session_id: int,
    user_id: int
) -> LearningSessionResponse:
    """
    Retrieve a learning session by ID.
    Validates session exists and is owned by the authenticated user.
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
            detail="You do not have permission to access this learning session"
        )

    return LearningSessionResponse.model_validate(session)


def get_journey_sessions(
    db: Session,
    journey_id: int,
    user_id: int
) -> LearningSessionListResponse:
    """
    Retrieve all sessions for a journey, ordered newest first.
    Validates journey exists and is owned by the authenticated user.
    """
    # Validate journey exists
    journey = get_learning_journey_by_id(db, journey_id)
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning journey not found"
        )

    # Validate journey ownership
    if journey.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access sessions for this journey"
        )

    sessions = repo_get_journey_sessions(db, journey_id)
    return LearningSessionListResponse(
        sessions=[
            LearningSessionResponse.model_validate(s)
            for s in sessions
        ],
        total=len(sessions)
    )


def complete_session(
    db: Session,
    session_id: int,
    user_id: int
) -> LearningSessionCompleteResponse:
    """
    Complete a learning session.
    Orchestrates the full completion workflow:
    1. Validate ownership
    2. Validate ACTIVE status
    3. Mark session COMPLETED
    4. Create learning activity (triggers achievement engine)
    5. Return response with integration flags
    """
    from app.services.learning_activity_service import record_learning_activity

    # Fetch session
    session = repo_get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning session not found"
        )

    # Validate ownership
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to complete this learning session"
        )

    # Validate status — reject duplicate completion
    if session.status == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Learning session is already completed"
        )

    # Validate status — reject archived sessions
    if session.status == "ARCHIVED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot complete an archived learning session"
        )

    # Initialize integration flags
    activity_created = False
    journey_updated = False
    streak_updated = False
    achievements_checked = False

    try:
        # Step 1: Mark session as COMPLETED
        repo_complete_session(db, session)
        logger.info(
            f"Learning session completed: session_id={session.id}, "
            f"user_id={user_id}"
        )

        # Step 2: Create learning activity
        # record_learning_activity internally calls evaluate_user_achievements
        try:
            record_learning_activity(
                db=db,
                user_id=user_id,
                activity_type="session_completed",
                entity_type="learning_session",
                entity_id=session.id,
                activity_data={
                    "session_uuid": session.uuid,
                    "journey_id": session.journey_id,
                    "title": session.title
                }
            )
            activity_created = True
            streak_updated = True  # Streak is read-computed from activities
            journey_updated = True  # Journey analytics updated via activities
            achievements_checked = True  # Evaluated inside record_learning_activity
            logger.info(
                f"Learning activity created for session_id={session.id}, "
                f"user_id={user_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to create learning activity for session_id={session.id}, "
                f"user_id={user_id}: {str(e)}"
            )
            # Activity creation failure should not block session completion
            # but we still want to raise to rollback the entire transaction
            raise

        db.commit()
        db.refresh(session)

        return LearningSessionCompleteResponse(
            id=session.id,
            uuid=session.uuid,
            journey_id=session.journey_id,
            title=session.title,
            status=session.status,
            started_at=session.started_at,
            ended_at=session.ended_at,
            activity_created=activity_created,
            journey_updated=journey_updated,
            streak_updated=streak_updated,
            achievements_checked=achievements_checked
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Session completion failed, transaction rolled back: "
            f"session_id={session_id}, user_id={user_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete learning session: {str(e)}"
        )


def archive_session(
    db: Session,
    session_id: int,
    user_id: int
) -> LearningSessionResponse:
    """
    Archive a learning session.
    Validates ownership and status before archiving.
    """
    # Fetch session
    session = repo_get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning session not found"
        )

    # Validate ownership
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to archive this learning session"
        )

    # Validate status — reject already archived
    if session.status == "ARCHIVED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Learning session is already archived"
        )

    try:
        repo_archive_session(db, session)
        db.commit()
        db.refresh(session)

        logger.info(
            f"Learning session archived: session_id={session.id}, "
            f"user_id={user_id}"
        )

        return LearningSessionResponse.model_validate(session)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Failed to archive learning session: "
            f"session_id={session_id}, user_id={user_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive learning session: {str(e)}"
        )
