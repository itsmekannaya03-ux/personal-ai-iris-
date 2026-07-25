"""Module Registry — tracks all registered modules with metadata."""

import time
from enum import Enum
from typing import Any


class ModuleState(Enum):
    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPED = "stopped"
    FAILED = "failed"


class ModuleInfo:
    __slots__ = ("id", "name", "version", "state", "health", "last_heartbeat", "metadata", "restart_count")

    def __init__(self, id: str, name: str, version: str = "1.0.0", metadata: dict | None = None):
        self.id = id
        self.name = name
        self.version = version
        self.state = ModuleState.UNREGISTERED
        self.health = True
        self.last_heartbeat = 0.0
        self.metadata = metadata or {}
        self.restart_count = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "state": self.state.value,
            "health": self.health,
            "last_heartbeat": self.last_heartbeat,
            "restart_count": self.restart_count,
            "metadata": self.metadata,
        }


class ModuleRegistry:
    def __init__(self):
        self._modules: dict[str, ModuleInfo] = {}

    def register(self, id: str, name: str, version: str = "1.0.0", metadata: dict | None = None) -> ModuleInfo:
        info = ModuleInfo(id, name, version, metadata)
        self._modules[id] = info
        return info

    def unregister(self, id: str):
        self._modules.pop(id, None)

    def get(self, id: str) -> ModuleInfo | None:
        return self._modules.get(id)

    def list_modules(self) -> list[ModuleInfo]:
        return list(self._modules.values())

    def list_by_state(self, state: ModuleState) -> list[ModuleInfo]:
        return [m for m in self._modules.values() if m.state == state]

    def set_state(self, id: str, state: ModuleState):
        info = self._modules.get(id)
        if info:
            info.state = state
            info.last_heartbeat = time.time()

    def heartbeat(self, id: str):
        info = self._modules.get(id)
        if info:
            info.last_heartbeat = time.time()
            info.health = True

    def mark_failed(self, id: str):
        info = self._modules.get(id)
        if info:
            info.state = ModuleState.FAILED
            info.health = False
            info.restart_count += 1

    def to_dict(self) -> list[dict]:
        return [m.to_dict() for m in self._modules.values()]
