"""
MentorIntent — enumerates all supported AI Mentor intent categories.

IntentResult — structured output from intent classification.

Easily extendable: add new members to MentorIntent and update
the keyword map in IntentClassifier.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MentorIntent(str, Enum):
    """
    Supported AI Mentor intent categories.

    Each intent maps to a user goal. Future intents (document search,
    coding assistant, scheduling, external APIs) can be added here
    without modifying the classifier or dispatcher logic.
    """

    GENERAL_CHAT = "GENERAL_CHAT"
    EXPLAIN_CONCEPT = "EXPLAIN_CONCEPT"
    LEARNING_PROGRESS = "LEARNING_PROGRESS"
    SESSION_SUMMARY = "SESSION_SUMMARY"
    LEARNING_JOURNEY = "LEARNING_JOURNEY"
    PROFILE_INFORMATION = "PROFILE_INFORMATION"
    LEARNING_ANALYTICS = "LEARNING_ANALYTICS"
    LEARNING_RECOMMENDATION = "LEARNING_RECOMMENDATION"
    PRACTICE_QUESTION = "PRACTICE_QUESTION"
    QUIZ = "QUIZ"
    DEBUG_CODE = "DEBUG_CODE"
    UNKNOWN = "UNKNOWN"


@dataclass
class IntentResult:
    """
    Structured output of intent classification.

    Attributes
    ----------
    intent : MentorIntent
        The classified intent.
    confidence : float
        Normalized confidence score (0.0 – 1.0).
    reason : str
        Human-readable explanation — useful for debugging/logging.
        Not exposed to end users unless in development mode.
    classification_time_ms : float
        Wall-clock time spent classifying (milliseconds).
    """

    intent: MentorIntent
    confidence: float
    reason: str
    classification_time_ms: float = 0.0
