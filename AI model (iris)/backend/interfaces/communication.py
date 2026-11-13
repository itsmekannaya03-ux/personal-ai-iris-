"""
CommunicationInterface — How the AI talks to the outside world.

Supported channels:
  - CLI (direct terminal input)
  - HTTP (FastAPI REST API)
  - WebSocket (real-time bidirectional)
  - Desktop app (future)
  - Mobile app (future)
"""

import logging
from typing import Optional, Callable, Any
from enum import Enum

logger = logging.getLogger("iris.communication")


class ChannelType(Enum):
    CLI = "cli"
    HTTP = "http"
    WEBSOCKET = "websocket"
    DESKTOP = "desktop"
    MOBILE = "mobile"


class CommunicationInterface:
    """
    Unified communication layer. All inbound and outbound
    communication flows through this interface.
    """

    def __init__(self):
        self._channels: dict[ChannelType, bool] = {
            ChannelType.CLI: True,
            ChannelType.HTTP: False,
            ChannelType.WEBSOCKET: False,
            ChannelType.DESKTOP: False,
            ChannelType.MOBILE: False,
        }
        self._listeners: dict[str, list[Callable]] = {}
        self._message_queue: list[dict] = []
        self._max_queue = 1000
        logger.info("Communication interface initialized")

    def open_channel(self, channel: ChannelType):
        self._channels[channel] = True
        logger.info(f"Channel opened: {channel.value}")

    def close_channel(self, channel: ChannelType):
        self._channels[channel] = False
        logger.info(f"Channel closed: {channel.value}")

    def is_channel_open(self, channel: ChannelType) -> bool:
        return self._channels.get(channel, False)

    def send(self, message: str, channel: ChannelType = ChannelType.CLI, metadata: Optional[dict] = None) -> bool:
        """Send a message through the specified channel."""
        if not self._channels.get(channel, False):
            logger.warning(f"Channel '{channel.value}' is not open")
            return False

        entry = {
            "type": "outgoing",
            "channel": channel.value,
            "message": message,
            "metadata": metadata or {},
            "timestamp": __import__("time").time(),
        }

        self._queue_message(entry)
        self._notify_listeners("message_sent", entry)
        return True

    def receive(self, message: str, channel: ChannelType = ChannelType.CLI, metadata: Optional[dict] = None) -> dict:
        """Receive and process an incoming message."""
        entry = {
            "type": "incoming",
            "channel": channel.value,
            "message": message,
            "metadata": metadata or {},
            "timestamp": __import__("time").time(),
        }

        self._queue_message(entry)
        self._notify_listeners("message_received", entry)
        return entry

    def _queue_message(self, entry: dict):
        self._message_queue.append(entry)
        if len(self._message_queue) > self._max_queue:
            self._message_queue.pop(0)

    def on(self, event: str, callback: Callable):
        """Register an event listener."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def _notify_listeners(self, event: str, data: Any):
        for callback in self._listeners.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Listener error ({event}): {e}")

    def get_message_history(self, limit: int = 50) -> list[dict]:
        return self._message_queue[-limit:]

    def get_status(self) -> dict:
        return {
            "channels": {c.value: o for c, o in self._channels.items()},
            "queue_size": len(self._message_queue),
            "listeners": {e: len(cbs) for e, cbs in self._listeners.items()},
        }
