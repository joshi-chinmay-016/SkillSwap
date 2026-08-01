"""
IntentClassifier — deterministic, rule-based intent classification.

Centralises all keyword mappings and priority rules.  No LLM calls,
no I/O, no side effects.  The LLM fallback stub is provided for
future extensibility but raises NotImplementedError today.
"""
import re
import time
import logging
from typing import Dict, List, Optional, Tuple

from app.ai.models.mentor_intent import MentorIntent, IntentResult
from app.ai.classifiers.intent_config import IntentClassificationConfig

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Rule-based intent classifier using centralised keyword mappings.

    Classification strategy (hybrid — Stage 1 only for now):
        Stage 1: Deterministic keyword / phrase matching
        Stage 2: (future) Optional LLM fallback for low-confidence results
    """

    def __init__(self, config: Optional[IntentClassificationConfig] = None):
        self._config = config or IntentClassificationConfig.default()
        self._keyword_map = self._build_keyword_map()
        self._priority = self._config.priority_order or self._default_priority()

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def classify(self, message: str) -> IntentResult:
        """
        Classify a user message into a MentorIntent.

        Parameters
        ----------
        message : str
            Raw user message text.

        Returns
        -------
        IntentResult with intent, confidence, reason, and timing.
        """
        t0 = time.perf_counter()

        if not message or not message.strip():
            elapsed = (time.perf_counter() - t0) * 1000
            return IntentResult(
                intent=MentorIntent.UNKNOWN,
                confidence=0.0,
                reason="Empty message.",
                classification_time_ms=elapsed,
            )

        normalised = self._normalise(message)

        # Collect all matching intents with their best confidence
        matches: List[Tuple[MentorIntent, float, str]] = []

        for intent, keyword_groups in self._keyword_map.items():
            best_conf = 0.0
            best_reason = ""
            for keywords, base_confidence in keyword_groups:
                conf, reason = self._match_keywords(normalised, keywords, base_confidence)
                if conf > best_conf:
                    best_conf = conf
                    best_reason = reason
            if best_conf > 0.0:
                matches.append((intent, best_conf, best_reason))

        if not matches:
            elapsed = (time.perf_counter() - t0) * 1000
            return IntentResult(
                intent=MentorIntent.UNKNOWN,
                confidence=0.0,
                reason="No keyword match found.",
                classification_time_ms=elapsed,
            )

        # Resolve by priority: among matches, pick the one with the
        # highest priority (lowest index in priority list).
        # If same priority, pick the higher confidence.
        matches.sort(key=lambda m: (self._priority_index(m[0]), -m[1]))
        best_intent, best_confidence, best_reason = matches[0]

        # Apply confidence threshold
        if best_confidence < self._config.confidence_threshold:
            elapsed = (time.perf_counter() - t0) * 1000
            return IntentResult(
                intent=MentorIntent.UNKNOWN,
                confidence=0.0,
                reason=f"Best match ({best_intent.value}) below threshold "
                       f"({best_confidence:.2f} < {self._config.confidence_threshold}).",
                classification_time_ms=elapsed,
            )

        elapsed = (time.perf_counter() - t0) * 1000
        return IntentResult(
            intent=best_intent,
            confidence=best_confidence,
            reason=best_reason,
            classification_time_ms=elapsed,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Keyword matching
    # ──────────────────────────────────────────────────────────────────────

    def _match_keywords(
        self,
        normalised: str,
        keywords: List[str],
        base_confidence: float,
    ) -> Tuple[float, str]:
        """
        Check how well `normalised` matches a keyword group.

        Returns (confidence, reason).
        """
        matched: List[str] = []
        for kw in keywords:
            if kw in normalised:
                matched.append(kw)

        if not matched:
            return 0.0, ""

        # Confidence scaling:
        #   - All keywords matched → full base_confidence
        #   - Partial match → scale proportionally, with a floor of 0.75 × base
        match_ratio = len(matched) / len(keywords)
        if match_ratio >= 1.0:
            confidence = base_confidence
        else:
            confidence = max(base_confidence * 0.75, base_confidence * match_ratio)

        # Clamp to [0.0, 1.0]
        confidence = min(1.0, max(0.0, round(confidence, 2)))

        reason = f"Matched keywords: {', '.join(matched)} (confidence={confidence:.2f})."
        return confidence, reason

    # ──────────────────────────────────────────────────────────────────────
    # Normalisation
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _normalise(text: str) -> str:
        """Lower-case, strip, collapse whitespace."""
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

    # ──────────────────────────────────────────────────────────────────────
    # Priority resolution
    # ──────────────────────────────────────────────────────────────────────

    def _priority_index(self, intent: MentorIntent) -> int:
        """Return position in priority list (lower = higher priority)."""
        try:
            return self._priority.index(intent)
        except ValueError:
            return len(self._priority)  # unlisted → lowest priority

    # ──────────────────────────────────────────────────────────────────────
    # Keyword map
    # ──────────────────────────────────────────────────────────────────────

    def _build_keyword_map(
        self,
    ) -> Dict[MentorIntent, List[Tuple[List[str], float]]]:
        """
        Merge the default keyword map with any configured overrides.

        Each entry is:  intent → [(keyword_list, base_confidence), ...]
        """
        base = self._default_keyword_map()
        overrides = self._config.keyword_overrides
        if overrides:
            for intent, groups in overrides.items():
                base[intent] = groups
        return base

    @staticmethod
    def _default_keyword_map() -> Dict[MentorIntent, List[Tuple[List[str], float]]]:
        """
        Centralised keyword → intent mapping.

        Structure:
            MentorIntent → [
                ([phrase_or_keyword, ...], base_confidence),
                ...
            ]

        Phrases (multi-word) are matched as substrings of the normalised
        input.  Single words are also matched as substrings.
        """
        return {
            # ── Concept explanation ──────────────────────────────────────
            MentorIntent.EXPLAIN_CONCEPT: [
                (["explain"], 0.90),
                (["teach me"], 0.90),
                (["what is"], 0.90),
                (["what are"], 0.90),
                (["how does"], 0.90),
                (["how do"], 0.85),
                (["understand"], 0.85),
                (["concept of"], 0.90),
                (["meaning of"], 0.85),
                (["define"], 0.85),
                (["tell me about"], 0.85),
                (["describe"], 0.80),
                (["difference between"], 0.90),
            ],

            # ── Learning progress ────────────────────────────────────────
            MentorIntent.LEARNING_PROGRESS: [
                (["my progress"], 0.95),
                (["learning progress"], 0.95),
                (["how many sessions"], 0.95),
                (["how much have i"], 0.90),
                (["completed sessions"], 0.95),
                (["sessions completed"], 0.95),
                (["my streak"], 0.90),
                (["current streak"], 0.90),
                (["how am i doing"], 0.85),
                (["my activity"], 0.80),
                (["track my"], 0.80),
            ],

            # ── Session summary ──────────────────────────────────────────
            MentorIntent.SESSION_SUMMARY: [
                (["summarize my"], 0.95),
                (["summarise my"], 0.95),
                (["summary of my"], 0.95),
                (["last session"], 0.90),
                (["session summary"], 0.95),
                (["session highlights"], 0.90),
                (["recap my"], 0.90),
                (["what did i learn"], 0.85),
                (["my last lesson"], 0.85),
            ],

            # ── Learning journey ─────────────────────────────────────────
            MentorIntent.LEARNING_JOURNEY: [
                (["my journey"], 0.95),
                (["learning journey"], 0.95),
                (["my roadmap"], 0.95),
                (["current journey"], 0.95),
                (["journey progress"], 0.90),
                (["milestone"], 0.85),
                (["learning path"], 0.90),
                (["my milestones"], 0.95),
                (["next milestone"], 0.90),
            ],

            # ── Profile information ──────────────────────────────────────
            MentorIntent.PROFILE_INFORMATION: [
                (["my profile"], 0.95),
                (["my skills"], 0.90),
                (["my interests"], 0.90),
                (["learning style"], 0.90),
                (["about me"], 0.85),
                (["my strengths"], 0.90),
                (["my weaknesses"], 0.90),
                (["strong topics"], 0.90),
                (["weak topics"], 0.90),
                (["my learning"], 0.75),
            ],

            # ── Learning analytics ───────────────────────────────────────
            MentorIntent.LEARNING_ANALYTICS: [
                (["my analytics"], 0.95),
                (["learning analytics"], 0.95),
                (["my insights"], 0.90),
                (["my statistics"], 0.95),
                (["my stats"], 0.90),
                (["learning trends"], 0.90),
                (["my performance"], 0.85),
                (["show analytics"], 0.95),
                (["weekly activity"], 0.90),
                (["monthly activity"], 0.90),
            ],

            # ── Learning recommendation ──────────────────────────────────
            MentorIntent.LEARNING_RECOMMENDATION: [
                (["recommend"], 0.90),
                (["suggest"], 0.85),
                (["what should i learn"], 0.95),
                (["what to learn"], 0.90),
                (["next topic"], 0.90),
                (["what next"], 0.85),
                (["what should i study"], 0.95),
                (["guide me"], 0.80),
            ],

            # ── Practice question ────────────────────────────────────────
            MentorIntent.PRACTICE_QUESTION: [
                (["practice question"], 0.95),
                (["give me a problem"], 0.90),
                (["practice exercise"], 0.95),
                (["challenge me"], 0.90),
                (["coding challenge"], 0.90),
                (["give me an exercise"], 0.90),
                (["practice problem"], 0.95),
            ],

            # ── Quiz ─────────────────────────────────────────────────────
            MentorIntent.QUIZ: [
                (["give me a quiz"], 0.95),
                (["quiz me"], 0.95),
                (["test me"], 0.90),
                (["assessment"], 0.85),
                (["evaluate me"], 0.85),
                (["quiz on"], 0.95),
                (["test my knowledge"], 0.95),
            ],

            # ── Debug code ───────────────────────────────────────────────
            MentorIntent.DEBUG_CODE: [
                (["debug"], 0.90),
                (["fix this"], 0.85),
                (["fix my"], 0.85),
                (["error in"], 0.85),
                (["bug in"], 0.85),
                (["not working"], 0.80),
                (["traceback"], 0.90),
                (["exception"], 0.80),
                (["help me debug"], 0.95),
                (["find the bug"], 0.90),
            ],

            # ── General chat ─────────────────────────────────────────────
            MentorIntent.GENERAL_CHAT: [
                (["hello"], 0.90),
                (["hi"], 0.85),
                (["hey"], 0.85),
                (["thanks"], 0.85),
                (["thank you"], 0.90),
                (["how are you"], 0.90),
                (["good morning"], 0.90),
                (["good evening"], 0.90),
                (["bye"], 0.85),
                (["goodbye"], 0.85),
            ],
        }

    @staticmethod
    def _default_priority() -> List[MentorIntent]:
        """
        Default priority order: specific intents first, general last.

        When "explain my progress" matches both EXPLAIN_CONCEPT and
        LEARNING_PROGRESS, the higher-priority intent
        (LEARNING_PROGRESS) wins.
        """
        return [
            # Data-retrieval intents (most specific)
            MentorIntent.LEARNING_PROGRESS,
            MentorIntent.SESSION_SUMMARY,
            MentorIntent.LEARNING_JOURNEY,
            MentorIntent.LEARNING_ANALYTICS,
            MentorIntent.PROFILE_INFORMATION,
            # Action-oriented intents
            MentorIntent.QUIZ,
            MentorIntent.PRACTICE_QUESTION,
            MentorIntent.DEBUG_CODE,
            # Advisory intents
            MentorIntent.LEARNING_RECOMMENDATION,
            # Knowledge intents
            MentorIntent.EXPLAIN_CONCEPT,
            # Catch-all
            MentorIntent.GENERAL_CHAT,
            MentorIntent.UNKNOWN,
        ]

    # ──────────────────────────────────────────────────────────────────────
    # LLM fallback stub (Stage 2 — future)
    # ──────────────────────────────────────────────────────────────────────

    def _llm_fallback(self, message: str) -> IntentResult:
        """
        Placeholder for future LLM-based classification.

        Will be invoked when rule-based confidence is below threshold
        and ``config.llm_fallback_enabled`` is True.
        """
        raise NotImplementedError(
            "LLM-based intent classification is not yet implemented. "
            "Enable only after Day 64 Part A2 is complete."
        )
