"""Event Dispatcher — system-wide event broadcasting."""

from typing import Callable, Any


class EventDispatcher:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    def on(self, event: str, handler: Callable):
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    def off(self, event: str, handler: Callable):
        if event in self._handlers:
            self._handlers[event] = [h for h in self._handlers[event] if h is not handler]

    def dispatch(self, event: str, data: dict | None = None):
        for handler in self._handlers.get(event, []):
            try:
                handler(data or {})
            except Exception:
                pass
        for handler in self._handlers.get("*", []):
            try:
                handler({"event": event, **(data or {})})
            except Exception:
                pass

    def clear(self):
        self._handlers.clear()
