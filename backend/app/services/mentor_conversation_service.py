"""
MentorConversationService — business logic & orchestration for persistent AI Mentor conversations.

Responsibilities:
    - User authorization (ensure user owns the conversation)
    - Auto-titling conversations on first user turn
    - Interfacing with MentorConversationRepository, MentorMessageRepository, and AIMentorService
    - Transaction management (commit/rollback)
"""
import logging
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.mentor_conversation import MentorConversation, ConversationStatus
from app.models.mentor_message import MentorMessage, MessageRole
from app.schemas.mentor_conversation import (
    MentorConversationCreate,
    MentorConversationUpdate,
    MentorConversationResponse,
    MentorConversationListResponse,
    MentorMessageResponse,
    MentorMessageListResponse,
    MentorConversationChatResponse,
)
from app.repositories import (
    mentor_conversation_repository as conv_repo,
    mentor_message_repository as msg_repo,
)
from app.ai.services.ai_mentor_service import AIMentorService

logger = logging.getLogger(__name__)


def create_conversation(
    db: Session,
    user_id: int,
    data: MentorConversationCreate,
) -> MentorConversation:
    """
    Create a new persistent conversation for user_id.
    Title defaults to 'New Conversation' if not supplied.
    """
    title = (data.title or "New Conversation").strip()
    try:
        conversation = conv_repo.create_conversation(
            db=db,
            user_id=user_id,
            title=title,
            journey_id=data.journey_id,
            session_id=data.session_id,
        )
        db.commit()
        db.refresh(conversation)
        return conversation
    except Exception as exc:
        db.rollback()
        logger.error("Failed to create conversation for user_id=%d: %s", user_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(exc)}",
        )


def list_conversations(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
) -> MentorConversationListResponse:
    """
    Return paginated conversations for a user.
    """
    conversations, total = conv_repo.list_user_conversations(
        db=db,
        user_id=user_id,
        page=page,
        page_size=page_size,
        status=status_filter,
    )
    items = [MentorConversationResponse.model_validate(c) for c in conversations]
    return MentorConversationListResponse(
        conversations=items,
        total=total,
        page=page,
        page_size=page_size,
    )


def get_conversation_or_404(
    db: Session,
    conversation_id: int,
    user_id: int,
) -> MentorConversation:
    """
    Retrieve conversation ensuring user_id ownership.
    Raises 404 if not found, 403 if user does not own it.
    """
    conversation = conv_repo.get_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    if conversation.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this conversation",
        )
    return conversation


def rename_conversation(
    db: Session,
    conversation_id: int,
    user_id: int,
    data: MentorConversationUpdate,
) -> MentorConversation:
    """Update conversation title."""
    conversation = get_conversation_or_404(db, conversation_id, user_id)
    try:
        conv_repo.update_conversation(db, conversation, title=data.title.strip())
        db.commit()
        db.refresh(conversation)
        return conversation
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rename conversation: {str(exc)}",
        )


def archive_conversation(
    db: Session,
    conversation_id: int,
    user_id: int,
) -> MentorConversation:
    """Set conversation status to ARCHIVED."""
    conversation = get_conversation_or_404(db, conversation_id, user_id)
    try:
        conv_repo.archive_conversation(db, conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive conversation: {str(exc)}",
        )


def delete_conversation(
    db: Session,
    conversation_id: int,
    user_id: int,
) -> None:
    """Permanently delete conversation and all messages."""
    conversation = get_conversation_or_404(db, conversation_id, user_id)
    try:
        conv_repo.delete_conversation(db, conversation)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(exc)}",
        )


def list_messages(
    db: Session,
    conversation_id: int,
    user_id: int,
    page: int = 1,
    page_size: int = 50,
) -> MentorMessageListResponse:
    """Return paginated messages for a conversation after verifying ownership."""
    get_conversation_or_404(db, conversation_id, user_id)
    messages, total = msg_repo.list_messages(
        db=db,
        conversation_id=conversation_id,
        page=page,
        page_size=page_size,
    )
    items = [MentorMessageResponse.model_validate(m) for m in messages]
    return MentorMessageListResponse(
        messages=items,
        total=total,
        page=page,
        page_size=page_size,
    )


def chat_in_conversation(
    db: Session,
    ai_mentor_service: AIMentorService,
    conversation_id: int,
    user_id: int,
    message_text: str,
) -> MentorConversationChatResponse:
    """
    Main Day 63 Part A2 chat orchestration:
        1. Authorize user ownership & active status
        2. Persist USER message
        3. Fetch recent bounded history (max settings.MENTOR_MAX_HISTORY_MESSAGES)
        4. Auto-generate title if this is the first turn
        5. Invoke AIMentorService with history & AI Context
        6. Persist ASSISTANT message
        7. Update conversation.last_message_at
        8. Commit transaction
        9. Return structured chat response
    """
    conversation = get_conversation_or_404(db, conversation_id, user_id)
    if conversation.status == ConversationStatus.ARCHIVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send messages to an archived conversation",
        )

    clean_message = message_text.strip()
    if not clean_message:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message content cannot be empty",
        )

    try:
        # ── 1. Fetch history BEFORE adding current message ─────────────────────
        limit = getattr(settings, "MENTOR_MAX_HISTORY_MESSAGES", 10)
        history = msg_repo.get_recent_history(db, conversation_id=conversation_id, limit=limit)

        # ── 2. Persist USER message ───────────────────────────────────────────
        user_msg = msg_repo.create_message(
            db=db,
            conversation_id=conversation_id,
            role=MessageRole.USER.value,
            content=clean_message,
        )

        # ── 3. Auto-title on first turn ───────────────────────────────────────
        if conversation.title == "New Conversation" and len(history) == 0:
            auto_title = clean_message[:40].strip()
            if len(clean_message) > 40:
                auto_title += "..."
            conv_repo.update_conversation(db, conversation, title=auto_title)

        # ── 4. Generate LLM response ─────────────────────────────────────────
        mentor_response = ai_mentor_service.chat_in_conversation(
            db=db,
            user_id=user_id,
            question=clean_message,
            history=history,
        )

        # ── 5. Persist ASSISTANT message ──────────────────────────────────────
        assistant_msg = msg_repo.create_message(
            db=db,
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT.value,
            content=mentor_response.response,
        )

        # ── 6. Update last_message_at timestamp ──────────────────────────────
        conv_repo.update_last_message_at(db, conversation, timestamp=assistant_msg.created_at)

        db.commit()
        db.refresh(user_msg)
        db.refresh(assistant_msg)
        db.refresh(conversation)

        return MentorConversationChatResponse(
            conversation_id=conversation.id,
            user_message=MentorMessageResponse.model_validate(user_msg),
            assistant_message=MentorMessageResponse.model_validate(assistant_msg),
            recommended_topics=mentor_response.recommended_topics,
            difficulty_level=mentor_response.difficulty_level,
            tool_used=mentor_response.tool_used,
            tool_success=mentor_response.tool_success,
            tool_execution_time=mentor_response.tool_execution_time,
            tool_data=mentor_response.tool_data,
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Error in chat_in_conversation for conv_id=%d: %s", conversation_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate mentor response: {str(exc)}",
        )


def retry_mentor_message(
    db: Session,
    ai_mentor_service: AIMentorService,
    conversation_id: int,
    message_id: int,
    user_id: int,
) -> MentorConversationChatResponse:
    """
    Retry generation for an existing USER message (e.g. if previous LLM call failed).
    Generates a new ASSISTANT message without duplicating the USER message.
    """
    conversation = get_conversation_or_404(db, conversation_id, user_id)
    if conversation.status == ConversationStatus.ARCHIVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot retry messages in an archived conversation",
        )

    target_msg = msg_repo.get_by_id(db, message_id)
    if not target_msg or target_msg.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User message not found in this conversation",
        )

    if target_msg.role.upper() != MessageRole.USER.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only USER messages can be retried",
        )

    try:
        limit = getattr(settings, "MENTOR_MAX_HISTORY_MESSAGES", 10)
        history = msg_repo.get_recent_history(db, conversation_id=conversation_id, limit=limit)
        # Filter out target_msg itself if present in history to avoid duplication
        history = [m for m in history if m.id != target_msg.id]

        mentor_response = ai_mentor_service.chat_in_conversation(
            db=db,
            user_id=user_id,
            question=target_msg.content,
            history=history,
        )

        assistant_msg = msg_repo.create_message(
            db=db,
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT.value,
            content=mentor_response.response,
        )

        conv_repo.update_last_message_at(db, conversation, timestamp=assistant_msg.created_at)

        db.commit()
        db.refresh(target_msg)
        db.refresh(assistant_msg)

        return MentorConversationChatResponse(
            conversation_id=conversation.id,
            user_message=MentorMessageResponse.model_validate(target_msg),
            assistant_message=MentorMessageResponse.model_validate(assistant_msg),
            recommended_topics=mentor_response.recommended_topics,
            difficulty_level=mentor_response.difficulty_level,
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Error retrying message_id=%d: %s", message_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry mentor response: {str(exc)}",
        )
