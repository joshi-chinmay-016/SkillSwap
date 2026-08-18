"""
Pydantic schemas for MentorConversation and MentorMessage.

Conventions match the existing project (Pydantic v2, from_attributes=True).
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ──────────────────────────────────────────────────────────────────────────────
# MentorMessage schemas
# ──────────────────────────────────────────────────────────────────────────────

class MentorMessageCreate(BaseModel):
    """
    Client sends only the message content.

    The backend always forces:
        role = USER

    Clients MUST NOT set role; the server owns it.
    """
    content: str = Field(
        min_length=1,
        max_length=8000,
        description="The learner's message content. Cannot be empty.",
    )


class MentorMessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MentorMessageListResponse(BaseModel):
    messages: List[MentorMessageResponse]
    total: int
    page: int
    page_size: int


# ──────────────────────────────────────────────────────────────────────────────
# MentorConversation schemas
# ──────────────────────────────────────────────────────────────────────────────

class MentorConversationCreate(BaseModel):
    """
    Request body for creating a new conversation.

    Do NOT include user_id — the authenticated user determines ownership.
    Both journey_id and session_id are optional.
    """
    title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Conversation title. Defaults to 'New Conversation' if not provided.",
    )
    journey_id: Optional[int] = Field(
        default=None,
        description="Optional: associate this conversation with a Learning Journey.",
    )
    session_id: Optional[int] = Field(
        default=None,
        description="Optional: associate this conversation with a Learning Session.",
    )


class MentorConversationUpdate(BaseModel):
    """
    Partial update — only title is modifiable by the client for now.
    """
    title: str = Field(
        min_length=1,
        max_length=255,
        description="New conversation title.",
    )


class MentorConversationResponse(BaseModel):
    id: int
    user_id: int
    journey_id: Optional[int] = None
    session_id: Optional[int] = None
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MentorConversationListResponse(BaseModel):
    conversations: List[MentorConversationResponse]
    total: int
    page: int
    page_size: int


# ──────────────────────────────────────────────────────────────────────────────
# Part A2 — Conversation-aware chat schemas
# ──────────────────────────────────────────────────────────────────────────────

class MentorConversationChatRequest(BaseModel):
    """
    Request body for conversation-aware chat.

    The client sends ONLY the message. Everything else (user_id,
    conversation history, AI context) is loaded server-side.
    """
    message: str = Field(
        min_length=1,
        max_length=4000,
        description="The learner's question or message.",
    )


class MentorConversationChatResponse(BaseModel):
    """
    Response after a conversation-aware chat turn.

    Includes both persisted messages and LLM metadata.
    """
    conversation_id: int
    user_message: MentorMessageResponse
    assistant_message: MentorMessageResponse
    recommended_topics: List[str] = []
    difficulty_level: str = "Intermediate"
    tool_used: Optional[str] = None
    tool_success: Optional[bool] = None
    tool_execution_time: Optional[int] = None
    tool_data: Optional[dict] = None


class MentorRetryResponse(BaseModel):
    """
    Response for a retry of a failed mentor generation.
    """
    conversation_id: int
    user_message: MentorMessageResponse
    assistant_message: MentorMessageResponse
    recommended_topics: List[str] = []
    difficulty_level: str = "Intermediate"
    tool_used: Optional[str] = None
    tool_success: Optional[bool] = None
    tool_execution_time: Optional[int] = None
    tool_data: Optional[dict] = None
