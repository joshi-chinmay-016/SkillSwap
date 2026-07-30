from typing import List, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class MentorChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
        description="The learner's question or message to the AI Mentor"
    )


class MentorChatResponse(BaseModel):
    response: str
    recommended_topics: List[str] = []
    difficulty_level: str = "Intermediate"


@dataclass
class PersonalizationMeta:
    """
    Structured personalization output from MentorIntelligenceEngine.
    Used by MentorPromptBuilder to inject learner-specific guidance.
    """
    difficulty_level: str = "Intermediate"
    use_analogies: bool = False
    skip_basics: bool = False
    build_prerequisites: bool = False
    style_instruction: str = ""
    recommended_topics: List[str] = field(default_factory=list)
    topic_is_weak: bool = False
    topic_is_strong: bool = False
    mode: str = "teaching"  # teaching | interview | revision | debugging
