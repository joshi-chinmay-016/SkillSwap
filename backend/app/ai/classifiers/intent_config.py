"""
IntentClassificationConfig — configurable parameters for intent classification.

All values have sensible defaults. Override via constructor for testing
or when loading from application settings.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from app.ai.models.mentor_intent import MentorIntent


@dataclass
class IntentClassificationConfig:
    """
    Configuration for the intent classification engine.

    Attributes
    ----------
    confidence_threshold : float
        Minimum confidence to accept a classification.
        Below this threshold the result is downgraded to UNKNOWN.
    llm_fallback_enabled : bool
        Future toggle — when True the classifier may invoke an LLM
        for low-confidence results.  Currently unused.
    priority_order : list[MentorIntent] | None
        Override the default intent priority.  When multiple intents
        match, the one appearing earliest in this list wins.
        None → use the built-in default.
    keyword_overrides : dict | None
        Override or extend the default keyword map.
        Keys are MentorIntent members; values are lists of
        (keywords, confidence) tuples identical to the default map
        structure.
    """

    confidence_threshold: float = 0.50
    llm_fallback_enabled: bool = False
    priority_order: Optional[List[MentorIntent]] = None
    keyword_overrides: Optional[Dict[MentorIntent, List[Tuple[List[str], float]]]] = None

    @staticmethod
    def default() -> "IntentClassificationConfig":
        """Return the production-default configuration."""
        return IntentClassificationConfig()
