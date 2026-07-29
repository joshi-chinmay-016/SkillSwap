from app.ai.services.session_summary_service import SessionSummaryService
from app.ai.schemas.session_summary import SessionSummaryRequest

class AISessionSummaryGenerator:
    """Compatibility wrapper for existing router imports.

    The original router expected an ``AISessionSummaryGenerator`` class with a
    ``generate`` method that accepted a ``SessionSummaryContext`` and returned a
    ``SessionSummaryRequest`` suitable for persisting.  The actual implementation
    lives in ``SessionSummaryService`` which provides a ``summarize`` method.
    This wrapper bridges the two so the router code can stay unchanged.
    """

    def __init__(self) -> None:
        self.service = SessionSummaryService()

    def generate(self, context):  # type: ignore[arg-type]
        """Generate a summary request from ``context``.

        ``context`` is the ``SessionSummaryContext`` defined in
        ``app.ai.schemas.session_summary``.  For now we only need the ``session_notes``
        field; we construct a minimal request with an empty notes string because
        the AI generation itself is out of scope for compilation.
        """
        # Create a placeholder request – real implementation will later use
        # ``context`` to build proper notes.
        request = SessionSummaryRequest(session_notes="")
        # The underlying service's ``summarize`` method returns a
        # ``SessionSummaryResponse``; the router expects a request‑like object.
        # We directly return the request here to satisfy type expectations.
        return request
