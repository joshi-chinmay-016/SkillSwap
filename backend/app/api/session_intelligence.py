from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    status
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.schemas.session_intelligence import (
    SessionNoteCreate,
    SessionNoteResponse,
    SessionTopicCreate,
    SessionTopicResponse,
    SessionActionItemCreate,
    SessionActionItemUpdate,
    SessionActionItemResponse,
    SessionIntelligenceResponse
)
from app.services import session_intelligence_service as intel_service
from app.core.rate_limiter import enforce_action_rate_limit

router = APIRouter(
    prefix="/sessions/{session_id}",
    tags=["Session Intelligence & Learning Capture"]
)


# --- Notes Endpoints ---
@router.post(
    "/notes",
    response_model=SessionNoteResponse,
    status_code=status.HTTP_200_OK
)
def save_notes(
    session_id: int,
    request: SessionNoteCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enforce_action_rate_limit("save_session_note", current_user.id, limit=60, window_seconds=60)
    return intel_service.save_session_note(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
        notes_data=request.model_dump()
    )


@router.get(
    "/notes",
    response_model=List[SessionNoteResponse]
)
def get_notes(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return intel_service.get_session_notes(
        db=db,
        session_id=session_id,
        user_id=current_user.id
    )


# --- Topics Endpoints ---
@router.post(
    "/topics",
    response_model=SessionTopicResponse,
    status_code=status.HTTP_201_CREATED
)
def add_topic(
    session_id: int,
    request: SessionTopicCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enforce_action_rate_limit("add_session_topic", current_user.id, limit=30, window_seconds=60)
    return intel_service.add_session_topic(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
        topic_name=request.topic_name,
        skill_id=request.skill_id,
        source=request.source or "user_input"
    )


@router.get(
    "/topics",
    response_model=List[SessionTopicResponse]
)
def get_topics(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return intel_service.get_session_topics(
        db=db,
        session_id=session_id,
        user_id=current_user.id
    )


# --- Action Items Endpoints ---
@router.post(
    "/action-items",
    response_model=SessionActionItemResponse,
    status_code=status.HTTP_201_CREATED
)
def create_action_item(
    session_id: int,
    request: SessionActionItemCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enforce_action_rate_limit("create_action_item", current_user.id, limit=30, window_seconds=60)
    return intel_service.create_session_action_item(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
        title=request.title,
        description=request.description,
        target_user_id=request.user_id,
        source="user_input"
    )


@router.get(
    "/action-items",
    response_model=List[SessionActionItemResponse]
)
def get_action_items(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return intel_service.get_session_action_items(
        db=db,
        session_id=session_id,
        user_id=current_user.id
    )


@router.patch(
    "/action-items/{item_id}",
    response_model=SessionActionItemResponse
)
def update_action_item(
    session_id: int,
    item_id: int,
    request: SessionActionItemUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return intel_service.update_action_item_status(
        db=db,
        session_id=session_id,
        item_id=item_id,
        user_id=current_user.id,
        status=request.status,
        title=request.title,
        description=request.description
    )


@router.delete(
    "/action-items/{item_id}"
)
def delete_action_item(
    session_id: int,
    item_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return intel_service.delete_session_action_item(
        db=db,
        session_id=session_id,
        item_id=item_id,
        user_id=current_user.id
    )


# --- Intelligence Generation Endpoints ---
@router.post(
    "/intelligence/generate",
    response_model=Optional[SessionIntelligenceResponse]
)
def generate_intelligence(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates grounded AI session intelligence from participant notes and topics.
    Rate limited with Redis sliding window.
    """
    enforce_action_rate_limit("generate_session_intelligence", current_user.id, limit=10, window_seconds=60)
    return intel_service.generate_session_intelligence(
        db=db,
        session_id=session_id,
        current_user_id=current_user.id
    )


@router.get(
    "/intelligence",
    response_model=Optional[SessionIntelligenceResponse]
)
def get_intelligence(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return intel_service.get_session_intelligence_report(
        db=db,
        session_id=session_id,
        user_id=current_user.id
    )
