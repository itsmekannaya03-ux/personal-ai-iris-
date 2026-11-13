"""
WebSocketManager — Real-time bidirectional communication.

Enables streaming responses, live status updates,
and push notifications to connected clients.
"""

import json
import logging
import asyncio
import time
from typing import Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("iris.websocket")


class WebSocketManager:
    """
    Manages WebSocket connections and message routing.
    Supports broadcasting and targeted messages.
    """

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._connection_map: dict[str, WebSocket] = {}
        logger.info("WebSocket manager initialized")

    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None):
        await websocket.accept()
        self._connections.add(websocket)
        cid = client_id or f"client_{int(time.time())}_{id(websocket)}"
        self._connection_map[cid] = websocket
        logger.info(f"WebSocket client connected: {cid}")
        return cid

    async def disconnect(self, websocket: WebSocket):
        self._connections.discard(websocket)
        to_remove = [cid for cid, ws in self._connection_map.items() if ws == websocket]
        for cid in to_remove:
            del self._connection_map[cid]
        logger.info(f"WebSocket client disconnected ({len(self._connections)} remaining)")

    async def send(self, websocket: WebSocket, data: dict):
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")
            await self.disconnect(websocket)

    async def broadcast(self, data: dict):
        dead = set()
        for ws in self._connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        for ws in dead:
            await self.disconnect(ws)

    async def send_to(self, client_id: str, data: dict):
        ws = self._connection_map.get(client_id)
        if ws:
            await self.send(ws, data)
        else:
            logger.warning(f"Client '{client_id}' not connected")

    async def handle_connection(self, websocket: WebSocket, brain=None):
        """Full connection handler — receive, process, respond."""
        client_id = await self.connect(websocket)
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = {"message": raw}

                message = data.get("message", "")
                if not message.strip():
                    await self.send(websocket, {"error": "Empty message"})
                    continue

                if message.lower() == "/status":
                    status = brain.status() if brain else {"status": "no_brain"}
                    await self.send(websocket, {"type": "status", "data": status})
                    continue

                if brain:
                    await self.send(websocket, {"type": "thinking", "message": "Processing..."})
                    result = brain.think(message)
                    response = {
                        "type": "response",
                        "data": {
                            "text": result.get("text", ""),
                            "action": result.get("action", ""),
                        }
                    }
                    await self.send(websocket, response)
                else:
                    await self.send(websocket, {"type": "response", "data": {"text": f"AI brain not available. You said: {message}"}})

        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
            await self.disconnect(websocket)

    def get_connection_count(self) -> int:
        return len(self._connections)

    def get_status(self) -> dict:
        return {
            "connections": len(self._connections),
            "clients": list(self._connection_map.keys()),
        }
