"""
SkillSwap Arena — Multi-Worker Redis Pub/Sub Coordination (Phase 6)

Allows real-time WebSocket notifications and session events to broadcast
across multiple FastAPI worker instances via Redis Pub/Sub.
"""
import json
import asyncio
import logging
from typing import Any, Callable, Dict, Optional

from app.core.config import settings
from app.infrastructure.redis.client import redis_client

logger = logging.getLogger("skillswap.pubsub")

# Global subscriber background task reference
_subscriber_task: Optional[asyncio.Task] = None
_running: bool = False


async def publish_event(channel: str, message_payload: Dict[str, Any]) -> bool:
    """
    Publishes an authoritative backend event to a Redis Pub/Sub channel.
    Falls back gracefully if Redis is unavailable.
    """
    try:
        raw_client = redis_client.get_raw_client()
        if raw_client and redis_client.is_available():
            serialized = json.dumps(message_payload, default=str)
            raw_client.publish(channel, serialized)
            return True
    except Exception as e:
        logger.debug(f"Pub/Sub publish error on channel {channel}: {e}")
    return False


async def publish_user_notification(user_id: int, payload: Dict[str, Any]) -> bool:
    """Publishes a targeted user notification across all FastAPI workers."""
    channel = getattr(settings, "REDIS_PUBSUB_CHANNEL", "skillswap:events")
    envelope = {
        "target_user_id": user_id,
        "payload": payload,
    }
    return await publish_event(channel, envelope)


async def start_pubsub_listener(message_handler: Callable[[int, Dict[str, Any]], Any]) -> None:
    """
    Launches an async background loop to listen on the Redis Pub/Sub channel.
    Routes received messages to local WebSocket active connections.
    """
    global _running, _subscriber_task
    _running = True

    async def _listener_loop():
        channel = getattr(settings, "REDIS_PUBSUB_CHANNEL", "skillswap:events")
        while _running:
            try:
                raw_client = redis_client.get_raw_client()
                if not raw_client or not redis_client.is_available():
                    await asyncio.sleep(5)
                    continue

                pubsub = raw_client.pubsub()
                pubsub.subscribe(channel)
                logger.info(f"Subscribed to Redis Pub/Sub channel: {channel}")

                while _running:
                    # Non-blocking get message
                    message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message.get("type") == "message":
                        try:
                            data = json.loads(message.get("data", "{}"))
                            target_user_id = data.get("target_user_id")
                            payload = data.get("payload")
                            if target_user_id and payload:
                                if asyncio.iscoroutinefunction(message_handler):
                                    await message_handler(target_user_id, payload)
                                else:
                                    message_handler(target_user_id, payload)
                        except Exception as parse_err:
                            logger.debug(f"Error handling Pub/Sub message: {parse_err}")

                    await asyncio.sleep(0.01)

            except Exception as loop_err:
                logger.debug(f"Pub/Sub listener reconnecting: {loop_err}")
                await asyncio.sleep(3)

    loop = asyncio.get_event_loop()
    _subscriber_task = loop.create_task(_listener_loop())


async def stop_pubsub_listener() -> None:
    """Stops the Redis Pub/Sub background listener gracefully on shutdown."""
    global _running, _subscriber_task
    _running = False
    if _subscriber_task:
        _subscriber_task.cancel()
        try:
            await _subscriber_task
        except asyncio.CancelledError:
            pass
        _subscriber_task = None
    logger.info("Redis Pub/Sub listener stopped.")
