import logging
from typing import Optional

from fastapi import (
    APIRouter,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from app.core.security import decode_access_token
from app.core.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: Optional[str] = Query(None),
):
    """
    WebSocket notification channel for user-specific real-time events.

    Security Requirements:
      1. Authentication: Requires a valid JWT token via ?token=<jwt_access_token>
      2. Authorization: Authenticated user ID (from token "sub") MUST match path user_id
      3. Violation Handling: Closes connection with 1008 (POLICY_VIOLATION) if unauthenticated or mismatched.
    """
    if not token:
        logger.warning("WebSocket connection rejected: missing token for user_id=%d", user_id)
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Missing authentication token",
        )
        return

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        logger.warning("WebSocket connection rejected: invalid or expired token for user_id=%d", user_id)
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or expired authentication token",
        )
        return

    try:
        authenticated_user_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        logger.warning("WebSocket connection rejected: malformed user ID in token claim")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Malformed user ID claim in token",
        )
        return

    if authenticated_user_id != user_id:
        logger.warning(
            "WebSocket connection rejected: user_id mismatch. Authenticated user=%d attempted to access user_id=%d channel",
            authenticated_user_id,
            user_id,
        )
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Forbidden: User ID mismatch",
        )
        return

    # Connection authenticated & authorized
    await manager.connect(user_id, websocket)
    logger.info("WebSocket connection established for authenticated user_id=%d", user_id)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info("WebSocket disconnected for user_id=%d", user_id)