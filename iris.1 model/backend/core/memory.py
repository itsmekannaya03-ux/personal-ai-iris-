"""
JarvisMemory — Persistent memory system for the AI.

Two-tier system:
  1. Short-term (episodic): Recent conversation history in-memory
  2. Long-term (semantic): Persistent file-based or vector storage
  
The AI remembers who you are, what you've discussed, and important facts.
"""

import json
import os
import time
import logging
import threading
import atexit
from enum import Enum
from typing import Optional, Any
from collections import deque
from datetime import datetime

logger = logging.getLogger("iris.memory")


class MemoryType(Enum):
    EPISODIC = "episodic"     # Recent conversations
    SEMANTIC = "semantic"     # Facts and knowledge
    PROCEDURAL = "procedural" # How to do things
    MUSCLE = "muscle"         # Learned patterns


class MemoryEntry:
    def __init__(self, key: str, value: Any, mtype: MemoryType = MemoryType.SEMANTIC, metadata: Optional[dict] = None):
        self.key = key
        self.value = value
        self.type = mtype
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 0

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "type": self.type.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
        }

    @classmethod
    def from_dict(cls, data: dict):
        entry = cls(data["key"], data["value"], MemoryType(data["type"]), data.get("metadata", {}))
        entry.created_at = data.get("created_at", time.time())
        entry.last_accessed = data.get("last_accessed", time.time())
        entry.access_count = data.get("access_count", 0)
        return entry


class JarvisMemory:
    """
    Full memory system. Persistent across sessions.
    Stores everything in a JSON file by default (vector DB optional).
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(
            os.path.expanduser("~"), ".iris", "memory", "iris_memory.json"
        )
        self._episodic: deque = deque(maxlen=100)  # Last 100 exchanges
        self._semantic: dict[str, MemoryEntry] = {}
        self._lock = threading.Lock()
        self._dirty = False
        self._auto_save_interval = 30  # seconds
        self._last_save = time.time()

        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self._load()
        atexit.register(self.shutdown)
        logger.info(f"Memory initialized: {self.storage_path}")

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                for entry_data in data.get("semantic", []):
                    entry = MemoryEntry.from_dict(entry_data)
                    self._semantic[entry.key] = entry
                for entry_data in data.get("episodic", []):
                    self._episodic.append(MemoryEntry.from_dict(entry_data))
                logger.info(f"Loaded {len(self._semantic)} semantic, {len(self._episodic)} episodic memories")
            except Exception as e:
                logger.error(f"Failed to load memory: {e}")

    def _save(self):
        if not self._dirty:
            return
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = {
                "semantic": [e.to_dict() for e in self._semantic.values()],
                "episodic": [e.to_dict() for e in self._episodic],
                "saved_at": time.time(),
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
            self._dirty = False
            self._last_save = time.time()
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def _auto_save(self):
        if time.time() - self._last_save > self._auto_save_interval and self._dirty:
            self._save()

    # ─── Public API ───────────────────────────────────────────

    def store(self, key: str, value: Any, mtype: MemoryType = MemoryType.SEMANTIC, metadata: Optional[dict] = None):
        with self._lock:
            entry = MemoryEntry(key, value, mtype, metadata)
            if mtype == MemoryType.EPISODIC:
                self._episodic.append(entry)
            else:
                self._semantic[key] = entry
            self._dirty = True
            self._auto_save()

    def retrieve(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._semantic.get(key)
            if entry:
                entry.last_accessed = time.time()
                entry.access_count += 1
                self._dirty = True
                return entry.value
            return None

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_lower = query.lower()
        results = []
        with self._lock:
            for key, entry in self._semantic.items():
                if query_lower in key.lower() or query_lower in str(entry.value).lower():
                    results.append({
                        "key": entry.key,
                        "value": entry.value,
                        "type": entry.type.value,
                        "relevance": entry.access_count,
                        "last_accessed": entry.last_accessed,
                    })
            results.sort(key=lambda x: x["relevance"], reverse=True)
            return results[:top_k]

    def get_recent(self, count: int = 10) -> list[dict]:
        with self._lock:
            return [
                {"key": e.key, "value": e.value, "timestamp": e.created_at}
                for e in list(self._episodic)[-count:]
            ]

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._semantic:
                del self._semantic[key]
                self._dirty = True
                return True
            return False

    def clear(self):
        with self._lock:
            self._semantic.clear()
            self._episodic.clear()
            self._dirty = True
            self._save()

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "semantic_count": len(self._semantic),
                "episodic_count": len(self._episodic),
                "storage_path": self.storage_path,
            }

    def save(self):
        with self._lock:
            self._save()

    def shutdown(self):
        try:
            self._save()
        except Exception:
            pass
