"""
SkillSwap Arena — Request Correlation & Metrics Middleware (Phase 8.7)

Attaches unique X-Request-ID to all incoming requests/responses, structures
observability logging, and instruments Prometheus request metrics.
"""
import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.infrastructure.metrics import (
    http_requests_total,
    http_request_duration_seconds
)

logger = logging.getLogger("skillswap.http")


def normalize_route_path(path: str) -> str:
    """
    Normalizes dynamic URL parameters to protect Prometheus from high-cardinality label explosion.
    Example: /admin/users/42/suspend -> /admin/users/{id}/suspend
    """
    parts = path.strip("/").split("/")
    normalized = []
    for part in parts:
        if part.isdigit():
            normalized.append("{id}")
        elif len(part) >= 32 and ("-" in part or part.isalnum()):
            normalized.append("{token}")
        else:
            normalized.append(part)
    return "/" + "/".join(normalized) if normalized else "/"


class CorrelationAndMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()
        method = request.method
        raw_path = request.url.path

        # Normalize path for safe low-cardinality metric labels
        normalized_handler = normalize_route_path(raw_path)

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception as exc:
            status_code = "500"
            duration = time.time() - start_time
            # Record failed metrics
            http_requests_total.labels(
                method=method, handler=normalized_handler, status_code=status_code
            ).inc()
            http_request_duration_seconds.labels(
                method=method, handler=normalized_handler
            ).observe(duration)

            logger.error(
                f'request_id="{request_id}" method={method} path="{raw_path}" status=500 duration_ms={round(duration * 1000, 2)} error="{str(exc)}"'
            )
            raise exc

        duration = time.time() - start_time

        # Skip recording the /metrics endpoint itself to keep metrics clean
        if raw_path != "/metrics":
            http_requests_total.labels(
                method=method, handler=normalized_handler, status_code=status_code
            ).inc()
            http_request_duration_seconds.labels(
                method=method, handler=normalized_handler
            ).observe(duration)

        response.headers["X-Request-ID"] = request_id

        if raw_path != "/metrics" and not raw_path.startswith("/health"):
            logger.info(
                f'request_id="{request_id}" method={method} path="{raw_path}" status={status_code} duration_ms={round(duration * 1000, 2)}'
            )

        return response
