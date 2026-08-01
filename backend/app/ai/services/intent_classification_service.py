"""
IntentClassificationService — business-layer wrapper around IntentClassifier.

Responsibilities:
    - Invoke IntentClassifier
    - Validate result
    - Handle fallback to UNKNOWN on errors
    - Log classification details (never logs sensitive data)
    - Track aggregate metrics for observability
"""
import logging
import time
from typing import Optional

from app.ai.classifiers.intent_classifier import IntentClassifier
from app.ai.classifiers.intent_config import IntentClassificationConfig
from app.ai.models.mentor_intent import MentorIntent, IntentResult

logger = logging.getLogger(__name__)


class IntentClassificationService:
    """
    Service layer for intent classification.

    Wraps IntentClassifier with error handling, logging, and metrics.
    """

    def __init__(
        self,
        config: Optional[IntentClassificationConfig] = None,
    ):
        self._config = config or IntentClassificationConfig.default()
        self._classifier = IntentClassifier(config=self._config)

        # ── Aggregate metrics ─────────────────────────────────────────────
        self._total_classifications: int = 0
        self._intent_frequency: dict[str, int] = {}
        self._unknown_count: int = 0
        self._cumulative_confidence: float = 0.0
        self._cumulative_latency_ms: float = 0.0

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def classify(
        self,
        user_id: int,
        conversation_id: Optional[int],
        message: str,
    ) -> IntentResult:
        """
        Classify a user message and return a validated IntentResult.

        On any internal failure the service returns UNKNOWN instead of
        crashing the mentor pipeline.

        Logged fields: user_id, conversation_id, intent, confidence,
                       classification_time_ms.
        Never logged:  API keys, prompts, AI context, conversation history.
        """
        t0 = time.perf_counter()

        try:
            result = self._classifier.classify(message)
        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            logger.error(
                "IntentClassificationService: classifier raised %s for user_id=%d: %s",
                type(exc).__name__,
                user_id,
                str(exc),
            )
            result = IntentResult(
                intent=MentorIntent.UNKNOWN,
                confidence=0.0,
                reason=f"Classifier error: {type(exc).__name__}",
                classification_time_ms=elapsed,
            )

        # ── Validate ──────────────────────────────────────────────────────
        result = self._validate(result)

        # ── Metrics ───────────────────────────────────────────────────────
        self._record_metrics(result)

        # ── Logging ───────────────────────────────────────────────────────
        logger.info(
            "IntentClassification: user_id=%d conversation_id=%s intent=%s "
            "confidence=%.2f time_ms=%.2f",
            user_id,
            conversation_id,
            result.intent.value,
            result.confidence,
            result.classification_time_ms,
        )

        return result

    def get_metrics(self) -> dict:
        """
        Return aggregated classification metrics.

        Useful for observability dashboards and intent-routing improvements.
        """
        total = self._total_classifications or 1  # avoid division by zero
        return {
            "total_classifications": self._total_classifications,
            "intent_frequency": dict(self._intent_frequency),
            "unknown_count": self._unknown_count,
            "unknown_rate": round(self._unknown_count / total, 4),
            "average_confidence": round(self._cumulative_confidence / total, 4),
            "average_latency_ms": round(self._cumulative_latency_ms / total, 2),
        }

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _validate(result: IntentResult) -> IntentResult:
        """
        Ensure the IntentResult is well-formed.

        Guards against:
        - confidence outside [0.0, 1.0]
        - intent not a valid MentorIntent member
        """
        # Clamp confidence
        result.confidence = min(1.0, max(0.0, result.confidence))

        # Verify enum membership
        if not isinstance(result.intent, MentorIntent):
            result.intent = MentorIntent.UNKNOWN
            result.confidence = 0.0
            result.reason = "Invalid intent — reset to UNKNOWN."

        return result

    def _record_metrics(self, result: IntentResult) -> None:
        """Update aggregate counters."""
        self._total_classifications += 1
        intent_key = result.intent.value
        self._intent_frequency[intent_key] = (
            self._intent_frequency.get(intent_key, 0) + 1
        )
        if result.intent == MentorIntent.UNKNOWN:
            self._unknown_count += 1
        self._cumulative_confidence += result.confidence
        self._cumulative_latency_ms += result.classification_time_ms
