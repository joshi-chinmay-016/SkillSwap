"""
MentorConversationRepository — database operations for MentorConversation.

Responsibilities: database queries only.
No business logic, no authorization, no LLM calls.
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.mentor_conversation import MentorConversation, ConversationStatus


# ──────────────────────────────────────────────────────────────────────────────
# Write operations
# ──────────────────────────────────────────────────────────────────────────────

def create_conversation(
    db: Session,
    user_id: int,
    title: str = "New Conversation",
    journey_id: Optional[int] = None,
    session_id: Optional[int] = None,
) -> MentorConversation:
    """Persist a new MentorConversation. Caller must commit."""
    conversation = MentorConversation(
        user_id=user_id,
        title=title,
        status=ConversationStatus.ACTIVE.value,
        journey_id=journey_id,
        session_id=session_id,
        last_message_at=None,
    )
    db.add(conversation)
    db.flush()
    return conversation


def update_conversation(
    db: Session,
    conversation: MentorConversation,
    **kwargs,
) -> MentorConversation:
    """
    Apply arbitrary field updates to a conversation.
    Caller must commit.

    Accepted kwargs: title, status, last_message_at
    """
    for field, value in kwargs.items():
        setattr(conversation, field, value)
    db.flush()
    return conversation


def archive_conversation(
    db: Session,
    conversation: MentorConversation,
) -> MentorConversation:
    """Set status to ARCHIVED. Caller must commit."""
    conversation.status = ConversationStatus.ARCHIVED.value
    db.flush()
    return conversation


def delete_conversation(
    db: Session,
    conversation: MentorConversation,
) -> None:
    """Hard-delete the conversation and cascade to messages. Caller must commit."""
    db.delete(conversation)
    db.flush()


def update_last_message_at(
    db: Session,
    conversation: MentorConversation,
    timestamp: Optional[datetime] = None,
) -> MentorConversation:
    """
    Update last_message_at to the given timestamp (defaults to now UTC).
    Caller must commit.
    """
    conversation.last_message_at = timestamp or datetime.now(timezone.utc)
    db.flush()
    return conversation


# ──────────────────────────────────────────────────────────────────────────────
# Read operations
# ──────────────────────────────────────────────────────────────────────────────

def get_by_id(
    db: Session,
    conversation_id: int,
) -> Optional[MentorConversation]:
    """Return a conversation by primary key, or None."""
    return (
        db.query(MentorConversation)
        .filter(MentorConversation.id == conversation_id)
        .first()
    )


def get_user_conversation(
    db: Session,
    conversation_id: int,
    user_id: int,
) -> Optional[MentorConversation]:
    """Return a conversation only if it belongs to user_id."""
    return (
        db.query(MentorConversation)
        .filter(
            MentorConversation.id == conversation_id,
            MentorConversation.user_id == user_id,
        )
        .first()
    )


def list_user_conversations(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
) -> tuple[List[MentorConversation], int]:
    """
    Return paginated conversations for a user, ordered by recent activity.

    Falls back to created_at desc when last_message_at is NULL so that
    brand-new conversations appear at the top of the list.

    Returns (conversations, total_count).
    """
    query = db.query(MentorConversation).filter(
        MentorConversation.user_id == user_id
    )

    if status:
        query = query.filter(MentorConversation.status == status.upper())

    total = query.count()

    conversations = (
        query
        .order_by(
            # NULLs last: put conversations with messages first
            MentorConversation.last_message_at.desc().nulls_last(),
            MentorConversation.created_at.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return conversations, total
