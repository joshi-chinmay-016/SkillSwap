"""
SkillSwap Arena — Prometheus Observability & Operational Metrics Engine (Phase 8.7)

Provides safe, low-cardinality, production-grade Prometheus metrics.
"""
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY
)

# Standard low-cardinality latency buckets (in seconds)
LATENCY_BUCKETS = (
    0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0
)

# 1. HTTP Traffic & Latency
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP request count partitioned by method, normalized route handler, and status code.",
    ["method", "handler", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds partitioned by method and route handler.",
    ["method", "handler"],
    buckets=LATENCY_BUCKETS,
)

# 2. WebSocket Connections
websocket_connections_active = Gauge(
    "websocket_connections_active",
    "Current count of active WebSocket connections across all users on this worker node."
)

# 3. Business Events
sessions_total = Counter(
    "sessions_total",
    "Total count of session lifecycle transitions.",
    ["status"],
)

booking_operations_total = Counter(
    "booking_operations_total",
    "Total count of peer booking attempts.",
    ["status"],
)

auth_attempts_total = Counter(
    "auth_attempts_total",
    "Total count of authentication attempts.",
    ["status", "provider"],
)

redis_operation_latency_seconds = Histogram(
    "redis_operation_latency_seconds",
    "Latency of Redis infrastructure operations.",
    ["operation"],
    buckets=(0.001, 0.002, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)


def get_metrics_response() -> tuple[bytes, str]:
    """Generates Prometheus scrapable metrics payload and MIME type."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
