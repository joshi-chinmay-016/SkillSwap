from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):

        self.active_connections = {}

    async def connect(
        self,
        user_id: int,
        websocket: WebSocket
    ):

        await websocket.accept()

        self.active_connections[
            user_id
        ] = websocket

    def disconnect(
        self,
        user_id: int
    ):

        self.active_connections.pop(
            user_id,
            None
        )

    async def send_notification(
        self,
        user_id: int,
        message: str
    ):

        websocket = (
            self.active_connections.get(
                user_id
            )
        )

        if websocket:

            print(
                f"Realtime notification sent to user {user_id}"
            )

            await websocket.send_json(
                {
                    "type": "notification",
                    "message": message
                }
            )

    async def send_notification_payload(
        self,
        user_id: int,
        payload: dict
    ):

        websocket = (
            self.active_connections.get(
                user_id
            )
        )

        if websocket:

            await websocket.send_json(
                payload
            )


manager = ConnectionManager()