"""
API Router for Persistent AI Mentor Conversations (Day 63 Parts A1 & A2).

Prefix: /mentor/conversations
Tags: AI Mentor Conversations
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.models.user import User
from app.schemas.mentor_conversation import (
    MentorConversationCreate,
    MentorConversationUpdate,
    MentorConversationResponse,
    MentorConversationListResponse,
    MentorMessageListResponse,
    MentorConversationChatRequest,
    MentorConversationChatResponse,
)
from app.services import mentor_conversation_service as service
from app.ai.dependencies import get_ai_mentor_service
from app.ai.services.ai_mentor_service import AIMentorService

router = APIRouter(
    prefix="/mentor/conversations",
    tags=["AI Mentor Conversations"],
)


@router.post(
    "",
    response_model=MentorConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new persistent AI Mentor conversation thread",
)
def create_conversation(
    data: MentorConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_conversation(db=db, user_id=current_user.id, data=data)


@router.get(
    "",
    response_model=MentorConversationListResponse,
    summary="List persistent conversations for current user",
)
def list_conversations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None, description="Filter by ACTIVE or ARCHIVED"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_conversations(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status_filter=status,
    )


@router.get(
    "/{conversation_id}",
    response_model=MentorConversationResponse,
    summary="Get conversation details by ID",
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = service.get_conversation_or_404(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    return MentorConversationResponse.model_validate(conversation)


@router.patch(
    "/{conversation_id}",
    response_model=MentorConversationResponse,
    summary="Rename conversation title",
)
def rename_conversation(
    conversation_id: int,
    data: MentorConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.rename_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        data=data,
    )


@router.patch(
    "/{conversation_id}/archive",
    response_model=MentorConversationResponse,
    summary="Archive conversation (read-only)",
)
def archive_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.archive_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation and all messages",
)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    return None


@router.get(
    "/{conversation_id}/messages",
    response_model=MentorMessageListResponse,
    summary="List paginated messages in chronological order",
)
def list_messages(
    conversation_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_messages(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{conversation_id}/chat",
    response_model=MentorConversationChatResponse,
    summary="Send persistent user message and generate AI Mentor response",
)
def chat_in_conversation(
    conversation_id: int,
    request: MentorConversationChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_mentor_service: AIMentorService = Depends(get_ai_mentor_service),
):
    return service.chat_in_conversation(
        db=db,
        ai_mentor_service=ai_mentor_service,
        conversation_id=conversation_id,
        user_id=current_user.id,
        message_text=request.message,
    )


@router.post(
    "/{conversation_id}/messages/{message_id}/retry",
    response_model=MentorConversationChatResponse,
    summary="Retry AI response generation for a USER message",
)
def retry_mentor_message(
    conversation_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_mentor_service: AIMentorService = Depends(get_ai_mentor_service),
):
    return service.retry_mentor_message(
        db=db,
        ai_mentor_service=ai_mentor_service,
        conversation_id=conversation_id,
        message_id=message_id,
        user_id=current_user.id,
    )
