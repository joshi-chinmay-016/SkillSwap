from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.schemas.learning_session import (
    LearningSessionCreate,
    LearningSessionResponse,
    LearningSessionListResponse,
    LearningSessionCompleteResponse,
)
from app.services import learning_session_service


# Router for journey-scoped endpoints: /journeys/{journey_id}/sessions
journey_sessions_router = APIRouter(
    prefix="/journeys",
    tags=["Learning Sessions"]
)

# Router for session-scoped endpoints: /sessions/{session_id}
sessions_router = APIRouter(
    prefix="/sessions",
    tags=["Learning Sessions"]
)


@journey_sessions_router.post(
    "/{journey_id}/sessions",
    response_model=LearningSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Learning Session",
    description="Create a new ACTIVE learning session for the specified journey. "
                "Verifies the journey exists and belongs to the authenticated user.",
    responses={
        201: {
            "description": "Session created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "user_id": 1,
                        "journey_id": 1,
                        "title": "Introduction to Python Basics",
                        "status": "ACTIVE",
                        "started_at": "2026-07-27T10:00:00Z",
                        "ended_at": None,
                        "created_at": "2026-07-27T10:00:00Z",
                        "updated_at": "2026-07-27T10:00:00Z"
                    }
                }
            }
        },
        403: {"description": "Journey belongs to another user"},
        404: {"description": "Journey not found"},
    }
)
def create_learning_session(
    journey_id: int,
    session_data: LearningSessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return learning_session_service.create_session(
        db, current_user.id, journey_id, session_data
    )


@journey_sessions_router.get(
    "/{journey_id}/sessions",
    response_model=LearningSessionListResponse,
    summary="Get Journey Sessions",
    description="Retrieve all learning sessions for the specified journey, "
                "ordered newest to oldest.",
    responses={
        200: {
            "description": "Sessions retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "sessions": [
                            {
                                "id": 2,
                                "uuid": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                                "user_id": 1,
                                "journey_id": 1,
                                "title": "Advanced Python Patterns",
                                "status": "ACTIVE",
                                "started_at": "2026-07-27T12:00:00Z",
                                "ended_at": None,
                                "created_at": "2026-07-27T12:00:00Z",
                                "updated_at": "2026-07-27T12:00:00Z"
                            }
                        ],
                        "total": 1
                    }
                }
            }
        },
        403: {"description": "Journey belongs to another user"},
        404: {"description": "Journey not found"},
    }
)
def get_journey_sessions(
    journey_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return learning_session_service.get_journey_sessions(
        db, journey_id, current_user.id
    )


@sessions_router.get(
    "/{session_id}",
    response_model=LearningSessionResponse,
    summary="Get Learning Session",
    description="Retrieve a single learning session by ID. "
                "Verifies the session belongs to the authenticated user.",
    responses={
        200: {
            "description": "Session retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "user_id": 1,
                        "journey_id": 1,
                        "title": "Introduction to Python Basics",
                        "status": "COMPLETED",
                        "started_at": "2026-07-27T10:00:00Z",
                        "ended_at": "2026-07-27T11:30:00Z",
                        "created_at": "2026-07-27T10:00:00Z",
                        "updated_at": "2026-07-27T11:30:00Z"
                    }
                }
            }
        },
        403: {"description": "Session belongs to another user"},
        404: {"description": "Session not found"},
    }
)
def get_learning_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return learning_session_service.get_session(
        db, session_id, current_user.id
    )


@sessions_router.patch(
    "/{session_id}/complete",
    response_model=LearningSessionCompleteResponse,
    summary="Complete a Learning Session",
    description="Mark a learning session as COMPLETED. Automatically creates a "
                "learning activity, triggers achievement evaluation, and updates "
                "streak and analytics data. Rejects duplicate completion.",
    responses={
        200: {
            "description": "Session completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "journey_id": 1,
                        "title": "Introduction to Python Basics",
                        "status": "COMPLETED",
                        "started_at": "2026-07-27T10:00:00Z",
                        "ended_at": "2026-07-27T11:30:00Z",
                        "activity_created": True,
                        "journey_updated": True,
                        "streak_updated": True,
                        "achievements_checked": True
                    }
                }
            }
        },
        403: {"description": "Session belongs to another user"},
        404: {"description": "Session not found"},
        409: {"description": "Session already completed or archived"},
    }
)
def complete_learning_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return learning_session_service.complete_session(
        db, session_id, current_user.id
    )


@sessions_router.patch(
    "/{session_id}/archive",
    response_model=LearningSessionResponse,
    summary="Archive a Learning Session",
    description="Mark a learning session as ARCHIVED. Archived sessions remain "
                "queryable but do not contribute to new activity or streak data.",
    responses={
        200: {
            "description": "Session archived successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "user_id": 1,
                        "journey_id": 1,
                        "title": "Introduction to Python Basics",
                        "status": "ARCHIVED",
                        "started_at": "2026-07-27T10:00:00Z",
                        "ended_at": None,
                        "created_at": "2026-07-27T10:00:00Z",
                        "updated_at": "2026-07-27T10:00:00Z"
                    }
                }
            }
        },
        403: {"description": "Session belongs to another user"},
        404: {"description": "Session not found"},
        409: {"description": "Session already archived"},
    }
)
def archive_learning_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return learning_session_service.archive_session(
        db, session_id, current_user.id
    )
