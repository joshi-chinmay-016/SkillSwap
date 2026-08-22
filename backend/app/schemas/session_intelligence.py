from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- Session Notes Schemas ---
class SessionNoteCreate(BaseModel):
    questions: Optional[List[str]] = Field(default_factory=list)
    concepts: Optional[List[str]] = Field(default_factory=list)
    struggles: Optional[List[str]] = Field(default_factory=list)
    takeaways: Optional[List[str]] = Field(default_factory=list)
    resources: Optional[List[str]] = Field(default_factory=list)
    next_steps: Optional[List[str]] = Field(default_factory=list)
    raw_notes: Optional[str] = Field(default="")


class SessionNoteResponse(BaseModel):
    id: int
    session_id: int
    user_id: int
    role: str
    notes_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Session Topics Schemas ---
class SessionTopicCreate(BaseModel):
    topic_name: str = Field(..., min_length=1, max_length=100)
    skill_id: Optional[int] = None
    source: Optional[str] = "user_input"


class SessionTopicResponse(BaseModel):
    id: int
    session_id: int
    topic_name: str
    skill_id: Optional[int] = None
    source: str
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Session Action Items Schemas ---
class SessionActionItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    user_id: Optional[int] = None  # Defaults to current user if not specified


class SessionActionItemUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|completed)$")
    title: Optional[str] = None
    description: Optional[str] = None


class SessionActionItemResponse(BaseModel):
    id: int
    session_id: int
    user_id: int
    title: str
    description: Optional[str] = None
    status: str
    source: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- Session Intelligence Schemas ---
class SessionIntelligenceResponse(BaseModel):
    id: int
    session_id: int
    status: str  # "completed", "insufficient_data", "failed"
    summary: Optional[str] = None
    topics_covered: List[Any] = Field(default_factory=list)
    skills_taught: List[Any] = Field(default_factory=list)
    skills_learned: List[Any] = Field(default_factory=list)
    key_takeaways: List[Any] = Field(default_factory=list)
    mentor_notes_summary: Optional[str] = None
    learner_notes_summary: Optional[str] = None
    recommended_next_steps: List[Any] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    action_items: List[SessionActionItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
