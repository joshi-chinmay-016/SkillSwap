import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.middleware.correlation import normalize_route_path

client = TestClient(app)


def test_correlation_id_generated_when_missing():
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    req_id = response.headers["x-request-id"]
    assert len(req_id) > 10


def test_correlation_id_preserved_when_provided():
    custom_id = "custom-client-trace-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == custom_id


def test_metrics_endpoint_returns_prometheus_format():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    text = response.text
    assert "http_requests_total" in text
    assert "http_request_duration_seconds" in text
    assert "websocket_connections_active" in text


def test_route_normalization_low_cardinality():
    assert normalize_route_path("/admin/users/42/suspend") == "/admin/users/{id}/suspend"
    assert normalize_route_path("/sessions/123/cancel") == "/sessions/{id}/cancel"
    assert normalize_route_path("/profiles/me") == "/profiles/me"
    assert normalize_route_path("/health") == "/health"
    assert normalize_route_path("/") == "/"


def test_health_endpoints():
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert "status" in res_health.json()

    res_redis = client.get("/health/redis")
    assert res_redis.status_code == 200
    assert "status" in res_redis.json()
