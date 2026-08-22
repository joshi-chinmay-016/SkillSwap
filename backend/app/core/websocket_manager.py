import logging
from fastapi import WebSocket
from typing import Dict, List

logger = logging.getLogger("skillswap.websocket")


class ConnectionManager:
    """
    Manages active WebSocket connections per authenticated user_id.
    Supports multiple concurrent tabs / connections per user and safe broadcasts.
    """
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(
        self,
        user_id: int,
        websocket: WebSocket
    ):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.debug(f"User {user_id} connected via WebSocket (active sockets: {len(self.active_connections[user_id])})")

    def disconnect(
        self,
        user_id: int,
        websocket: WebSocket | None = None
    ):
        if user_id in self.active_connections:
            if websocket and websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            else:
                self.active_connections.pop(user_id, None)

            if user_id in self.active_connections and not self.active_connections[user_id]:
                self.active_connections.pop(user_id, None)
            logger.debug(f"User {user_id} disconnected from WebSocket")

    async def send_notification(
        self,
        user_id: int,
        message: str
    ):
        await self.send_notification_payload(
            user_id,
            {
                "type": "NOTIFICATION",
                "message": message
            }
        )

    async def send_notification_payload(
        self,
        user_id: int,
        payload: dict
    ):
        sockets = self.active_connections.get(user_id, [])
        dead_sockets = []
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception as e:
                logger.debug(f"Failed to send WS payload to user {user_id}: {e}")
                dead_sockets.append(ws)

        for dead in dead_sockets:
            if dead in sockets:
                sockets.remove(dead)
        if not sockets and user_id in self.active_connections:
            self.active_connections.pop(user_id, None)


manager = ConnectionManager()