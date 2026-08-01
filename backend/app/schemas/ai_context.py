"""
Pydantic schemas for the Learning AI Profile (AIContext) endpoints.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AIContextResponse(BaseModel):
    """Full read-only representation of the user's AI learning profile."""

    id: int
    user_id: int
    overall_summary: Optional[str] = None
    strong_topics: List[str] = Field(default_factory=list)
    weak_topics: List[str] = Field(default_factory=list)
    learning_interests: List[str] = Field(default_factory=list)
    recommended_topics: List[str] = Field(default_factory=list)
    learning_style: Optional[str] = None
    completed_sessions: int = 0
    context_version: int = 1
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIContextUpdate(BaseModel):
    """
    User-editable fields of the AI learning profile.

    Only learning_interests and learning_style can be manually overridden.
    strong_topics, weak_topics, and recommended_topics are data-driven
    and can only be changed via profile regeneration.
    """

    learning_interests: Optional[List[str]] = None
    learning_style: Optional[str] = None
