from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class SessionSummaryCreate(BaseModel):
    """Schema for creating a new session summary (from manual API or AI pipeline)."""

    summary: str = Field(
        ...,
        min_length=1,
        description="High-level summary of what the learner accomplished",
        json_schema_extra={
            "examples": ["The learner successfully explained Binary Search and its time complexity."]
        }
    )

    key_takeaways: List[str] = Field(
        default_factory=list,
        description="Major concepts and topics covered in this session",
        json_schema_extra={
            "examples": [["Binary Search", "Divide and Conquer", "O(log n)"]]
        }
    )

    strengths: List[str] = Field(
        default_factory=list,
        description="Areas where the learner demonstrated strong understanding",
        json_schema_extra={
            "examples": [["Correct explanation of the algorithm", "Good use of examples"]]
        }
    )

    weaknesses: List[str] = Field(
        default_factory=list,
        description="Areas that need further improvement or practice",
        json_schema_extra={
            "examples": [["Forgot to handle edge cases", "Unclear on off-by-one errors"]]
        }
    )

    follow_up_topics: List[str] = Field(
        default_factory=list,
        description="Recommended topics for the next learning session",
        json_schema_extra={
            "examples": [["Lower Bound", "Upper Bound", "Binary Search on answer space"]]
        }
    )


class SessionSummaryUpdate(BaseModel):
    """Schema for updating an existing session summary. All fields optional."""

    summary: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Updated high-level summary"
    )

    key_takeaways: Optional[List[str]] = Field(
        default=None,
        description="Updated key takeaways"
    )

    strengths: Optional[List[str]] = Field(
        default=None,
        description="Updated strengths"
    )

    weaknesses: Optional[List[str]] = Field(
        default=None,
        description="Updated weaknesses"
    )

    follow_up_topics: Optional[List[str]] = Field(
        default=None,
        description="Updated follow-up topics"
    )


class SessionSummaryResponse(BaseModel):
    """Full session summary response — returned by GET and PUT endpoints."""

    id: int
    uuid: str
    session_id: int
    summary: str
    key_takeaways: List[str]
    strengths: List[str]
    weaknesses: List[str]
    follow_up_topics: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionSummaryCreateResponse(BaseModel):
    """Lightweight response returned immediately after creation."""

    summary_id: int
    uuid: str
    session_id: int
    created_at: datetime

    class Config:
        from_attributes = True
