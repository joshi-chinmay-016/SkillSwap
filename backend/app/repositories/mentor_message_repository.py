"""
MentorMessageRepository — database operations for MentorMessage.

Responsibilities: database queries only.
No business logic, no LLM calls.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.mentor_message import MentorMessage, MessageRole


def create_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
) -> MentorMessage:
    """
    Persist a message to the database. Caller must commit.
    """
    message = MentorMessage(
        conversation_id=conversation_id,
        role=role.upper(),
        content=content.strip(),
    )
    db.add(message)
    db.flush()
    return message


def get_by_id(
    db: Session,
    message_id: int,
) -> Optional[MentorMessage]:
    """Return a message by ID, or None."""
    return (
        db.query(MentorMessage)
        .filter(MentorMessage.id == message_id)
        .first()
    )


def list_messages(
    db: Session,
    conversation_id: int,
    page: int = 1,
    page_size: int = 50,
) -> tuple[List[MentorMessage], int]:
    """
    Return paginated messages for a conversation ordered chronologically (created_at asc).
    Returns (messages, total_count).
    """
    query = db.query(MentorMessage).filter(
        MentorMessage.conversation_id == conversation_id
    )
    total = query.count()

    messages = (
        query
        .order_by(MentorMessage.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return messages, total


def get_recent_history(
    db: Session,
    conversation_id: int,
    limit: int = 10,
) -> List[MentorMessage]:
    """
    Fetch the most recent N messages for a conversation ordered chronologically.
    Used for bounded context retrieval when constructing LLM prompts.
    """
    recent = (
        db.query(MentorMessage)
        .filter(MentorMessage.conversation_id == conversation_id)
        .order_by(MentorMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    # Reverse so they are in chronological order (oldest -> newest)
    return list(reversed(recent))
