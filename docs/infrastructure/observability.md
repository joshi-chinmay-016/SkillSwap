# Observability, Prometheus & Tracing

SkillSwap Arena provides full operational visibility through Prometheus metrics scraping, structured request correlation, and pre-provisioned Grafana dashboards.

---

## 1. Low-Cardinality Prometheus Metrics (`/metrics`)

Operational metrics are instrumented via `app/infrastructure/metrics.py`:

```
# HTTP Traffic & Latencies
http_requests_total{method="GET", handler="/sessions/{id}", status_code="200"}
http_request_duration_seconds_bucket{le="0.1", method="POST", handler="/auth/login"}

# Real-Time WebSocket Connections
websocket_connections_active 42

# Business Operations
sessions_total{status="completed"} 128
auth_attempts_total{status="success", provider="password"} 310
booking_operations_total{status="success"} 95
```

### Protection Against High-Cardinality Explosion
Path normalization (`normalize_route_path`) strips raw database IDs and tokens (e.g. `/admin/users/42/suspend` → `/admin/users/{id}/suspend`), ensuring metric label cardinality remains constant under heavy traffic.

---

## 2. Request Correlation (`X-Request-ID`)

- Every request is tagged with a unique UUID4 trace identifier by `CorrelationAndMetricsMiddleware`.
- The `X-Request-ID` is included in response headers and logged in all log entries for request tracing.

---

## 3. Health Diagnostics

- `GET /health`: Core server health summary.
- `GET /health/redis`: Real-time Redis latency and cluster status.
- `GET /admin/system/health`: Diagnostic latency breakdown (DB latency in ms, Redis latency in ms, uptime).
