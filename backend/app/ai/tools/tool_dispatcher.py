"""
ToolDispatcher — resolves and executes tools based on classified intent.

Contains zero business logic.  Purely dispatches to the correct tool
via the ToolRegistry, handles failures gracefully, and tracks metrics.
"""
import logging
import time
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.ai.models.mentor_intent import IntentResult, MentorIntent
from app.ai.tools.mentor_tool import MentorTool, ToolResult
from app.ai.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolDispatcher:
    """
    Dispatches tool execution based on intent classification results.

    Logging policy:
        Logged:  tool name, execution time, success/failure, user_id
        Never:   sensitive profile data, prompts, API keys
    """

    def __init__(self, registry: ToolRegistry, timeout_seconds: int = 5):
        self._registry = registry
        self._timeout_seconds = timeout_seconds

        # ── Aggregate metrics ─────────────────────────────────────────────
        self._total_dispatches: int = 0
        self._tool_usage: Dict[str, int] = {}
        self._success_count: int = 0
        self._failure_count: int = 0
        self._cumulative_latency_ms: float = 0.0

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def dispatch(
        self,
        db: Session,
        user_id: int,
        intent_result: IntentResult,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Optional[ToolResult]:
        """
        Resolve and execute the tool for the classified intent.

        Returns
        -------
        ToolResult on successful resolution (even if tool execution fails).
        None if no tool is registered for the intent (e.g. GENERAL_CHAT).
        """
        tool = self._registry.resolve(intent_result.intent)
        if tool is None:
            logger.debug(
                "ToolDispatcher: no tool registered for intent=%s",
                intent_result.intent.value,
            )
            return None

        params = parameters or {}

        logger.info(
            "ToolDispatcher: dispatching %s for user_id=%d intent=%s",
            tool.name,
            user_id,
            intent_result.intent.value,
        )

        t0 = time.perf_counter()
        try:
            result = tool.execute(db=db, user_id=user_id, parameters=params)
        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            logger.error(
                "ToolDispatcher: %s raised unhandled exception for user_id=%d: %s",
                tool.name,
                user_id,
                str(exc),
            )
            result = ToolResult(
                tool=tool.name,
                success=False,
                error=f"Dispatch error: {str(exc)}",
                execution_time_ms=elapsed,
            )

        elapsed = (time.perf_counter() - t0) * 1000

        # ── Metrics ───────────────────────────────────────────────────────
        self._total_dispatches += 1
        self._tool_usage[tool.name] = self._tool_usage.get(tool.name, 0) + 1
        self._cumulative_latency_ms += elapsed
        if result.success:
            self._success_count += 1
        else:
            self._failure_count += 1

        # ── Logging ───────────────────────────────────────────────────────
        logger.info(
            "ToolDispatcher: %s completed — success=%s time_ms=%.2f user_id=%d",
            tool.name,
            result.success,
            elapsed,
            user_id,
        )

        return result

    def get_metrics(self) -> dict:
        """Return aggregated dispatch metrics for observability."""
        total = self._total_dispatches or 1
        return {
            "total_dispatches": self._total_dispatches,
            "tool_usage": dict(self._tool_usage),
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "success_rate": round(self._success_count / total, 4),
            "failure_rate": round(self._failure_count / total, 4),
            "average_latency_ms": round(self._cumulative_latency_ms / total, 2),
        }
