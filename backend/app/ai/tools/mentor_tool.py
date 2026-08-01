"""
MentorTool — abstract base class for all AI Mentor internal tools.

Every tool that retrieves platform data inherits from MentorTool and
registers its supported intents.  The ToolDispatcher resolves and
executes the correct tool based on the classified intent.
"""
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.ai.models.mentor_intent import MentorIntent

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Exceptions
# ──────────────────────────────────────────────────────────────────────────────


class ToolValidationError(Exception):
    """Raised when tool input validation fails (missing params, bad ownership)."""
    pass


class ToolTimeoutError(Exception):
    """Raised when tool execution exceeds the configured timeout."""
    pass


# ──────────────────────────────────────────────────────────────────────────────
# ToolResult
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class ToolResult:
    """
    Standard response structure returned by every tool.

    Consistent shape allows the prompt builder and dispatcher to
    handle all tools uniformly.
    """

    tool: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: str = ""
    execution_time_ms: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────────────────────
# MentorTool ABC
# ──────────────────────────────────────────────────────────────────────────────


class MentorTool(ABC):
    """
    Base class for AI Mentor internal tools.

    Subclasses must implement:
        - name            (property)
        - description     (property)
        - supported_intents (property)
        - _execute        (core logic)

    Optionally override:
        - validate        (input validation before execution)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this tool does."""
        ...

    @property
    @abstractmethod
    def supported_intents(self) -> List[MentorIntent]:
        """List of intents this tool can handle."""
        ...

    def validate(
        self,
        db: Session,
        user_id: int,
        parameters: Dict[str, Any],
    ) -> None:
        """
        Validate inputs before execution.

        Override in subclasses to enforce authentication, ownership,
        required parameters, etc.  Raises ToolValidationError on failure.

        Default implementation validates only that user_id is positive.
        """
        if not user_id or user_id <= 0:
            raise ToolValidationError("Valid authenticated user_id is required.")

    def execute(
        self,
        db: Session,
        user_id: int,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """
        Public entry point.  Validates, executes, and returns ToolResult.

        Subclasses should NOT override this method — override _execute instead.
        """
        params = parameters or {}

        try:
            self.validate(db, user_id, params)
        except ToolValidationError as exc:
            logger.warning(
                "%s: validation failed for user_id=%d: %s",
                self.name, user_id, str(exc),
            )
            return ToolResult(
                tool=self.name,
                success=False,
                error=f"Validation error: {str(exc)}",
            )

        t0 = time.perf_counter()
        try:
            data = self._execute(db, user_id, params)
            elapsed = (time.perf_counter() - t0) * 1000
            return ToolResult(
                tool=self.name,
                success=True,
                data=data,
                execution_time_ms=elapsed,
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            logger.error(
                "%s: execution failed for user_id=%d: %s",
                self.name, user_id, str(exc),
            )
            return ToolResult(
                tool=self.name,
                success=False,
                error=str(exc),
                execution_time_ms=elapsed,
            )

    @abstractmethod
    def _execute(
        self,
        db: Session,
        user_id: int,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Core tool logic — override in subclasses.

        Must return a plain dict (JSON-serialisable).
        Raise any exception on failure — the base class wraps it
        into a ToolResult with success=False.
        """
        ...
