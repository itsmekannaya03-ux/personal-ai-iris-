"""Communication Bus — pub/sub message passing between modules."""

import asyncio
import json
import time
import uuid
from typing import Callable, Any
from collections import defaultdict


class Message:
    __slots__ = ("id", "type", "source", "target", "timestamp", "body", "correlation_id", "ttl")

    def __init__(
        self,
        type: str,
        source: str,
        target: str = "*",
        body: dict | None = None,
        correlation_id: str | None = None,
        ttl: int = 30000,
    ):
        self.id = f"msg_{uuid.uuid4().hex[:12]}"
        self.type = type
        self.source = source
        self.target = target
        self.timestamp = time.time()
        self.body = body or {}
        self.correlation_id = correlation_id
        self.ttl = ttl

    def to_dict(self) -> dict:
        return {s: getattr(self, s) for s in self.__slots__}

    def expired(self) -> bool:
        return (time.time() - self.timestamp) * 1000 > self.ttl


class MessageBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._pending_requests: dict[str, asyncio.Future] = {}

    def publish(self, message: Message):
        for handler in self._subscribers.get(message.target, []):
            try:
                handler(message)
            except Exception:
                pass
        for handler in self._subscribers.get("*", []):
            try:
                handler(message)
            except Exception:
                pass

    def subscribe(self, target: str, handler: Callable):
        self._subscribers[target].append(handler)

    def unsubscribe(self, target: str, handler: Callable):
        if handler in self._subscribers.get(target, []):
            self._subscribers[target].remove(handler)

    async def request(self, target: str, body: dict, timeout: float = 30.0) -> dict:
        msg = Message("request", "core_matrix", target, body)
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[msg.id] = future

        def response_handler(resp_msg: Message):
            if resp_msg.correlation_id == msg.id and not future.done():
                future.set_result(resp_msg.body)

        self.subscribe(target, response_handler)
        self.publish(msg)

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return {"error": "timeout", "message": f"No response from {target} within {timeout}s"}
        finally:
            self._pending_requests.pop(msg.id, None)
            self.unsubscribe(target, response_handler)

    def respond(self, request_msg: Message, body: dict):
        response = Message(
            type="response",
            source=request_msg.target,
            target=request_msg.source,
            body=body,
            correlation_id=request_msg.id,
        )
        self.publish(response)

    def broadcast(self, event: str, body: dict | None = None):
        msg = Message("event", "core_matrix", "*", {"event": event, **(body or {})})
        self.publish(msg)
