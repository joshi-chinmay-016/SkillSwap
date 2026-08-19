"""
WebSocket Security Hardening Test Suite (Day 77).

Verifies:
  1. Valid token + matching user_id -> connection accepted and registered in ConnectionManager.
  2. Missing token -> connection rejected with 1008 Policy Violation.
  3. Invalid token -> connection rejected with 1008 Policy Violation.
  4. Expired token -> connection rejected with 1008 Policy Violation.
  5. Mismatched user_id (token user 1 != path user 2) -> connection rejected with 1008.
  6. Disconnect -> user unregistered from ConnectionManager.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.security import create_access_token
from app.core.websocket_manager import manager
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_websocket_missing_token_rejected(client: TestClient):
    """Connecting without ?token= query parameter MUST fail with WS close code 1008."""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/1"):
            pass
    assert exc_info.value.code == 1008


def test_websocket_invalid_token_rejected(client: TestClient):
    """Connecting with an invalid JWT string MUST fail with WS close code 1008."""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/1?token=invalid.jwt.string"):
            pass
    assert exc_info.value.code == 1008


def test_websocket_expired_token_rejected(client: TestClient):
    """Connecting with an expired JWT MUST fail with WS close code 1008."""
    from datetime import timedelta
    expired_token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/ws/1?token={expired_token}"):
            pass
    assert exc_info.value.code == 1008


def test_websocket_user_mismatch_rejected(client: TestClient):
    """Token for user_id=1 attempting to connect to /ws/2 MUST fail with 1008."""
    token = create_access_token({"sub": "1"})
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/ws/2?token={token}"):
            pass
    assert exc_info.value.code == 1008


def test_websocket_valid_token_matching_user_accepted(client: TestClient):
    """Token for user_id=1 connecting to /ws/1 MUST be accepted and registered in ConnectionManager."""
    token = create_access_token({"sub": "1"})
    user_id = 1

    assert user_id not in manager.active_connections

    with client.websocket_connect(f"/ws/1?token={token}") as websocket:
        assert user_id in manager.active_connections
        assert manager.active_connections[user_id] is not None

    # Upon disconnect, ConnectionManager must be cleaned up
    assert user_id not in manager.active_connections
