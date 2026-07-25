import json
import time
import logging
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger("igris.memory.deep")


class DeepLayer:
    """
    Permanent memory — never auto-deleted.
    Only removable by explicit user command.
    If user later contradicts a fact, it gets flagged for confirmation.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self._storage_path = Path(storage_path or self._default_path())
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._memories: dict[str, dict] = {}
        self._load()
        logger.info(f"DeepLayer ready ({len(self._memories)} items)")

    def _default_path(self) -> str:
        return str(Path.home() / ".igris" / "memory_deep.json")

    def _load(self):
        try:
            if self._storage_path.exists():
                with open(self._storage_path) as f:
                    self._memories = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load deep memory: {e}")
            self._memories = {}

    def _save(self):
        try:
            self._storage_path.write_text(json.dumps(self._memories, indent=2))
        except Exception as e:
            logger.error(f"Failed to save deep memory: {e}")

    def store(self, key: str, content: str, metadata: dict = None) -> dict:
        with self._lock:
            now = time.time()
            existing = self._memories.get(key)
            if existing and existing.get("content") != content:
                return {"entry": self._flag_conflict(key, existing, content), "conflict": True}
            entry = {
                "key": key,
                "content": content,
                "timestamp": now,
                "mention_count": (existing.get("mention_count", 0) + 1) if existing else 1,
                "metadata": metadata or {},
            }
            self._memories[key] = entry
            self._save()
            return {"entry": entry, "conflict": False}

    def _flag_conflict(self, key: str, existing: dict, new_content: str) -> dict:
        entry = {
            "key": key,
            "content": existing.get("content", ""),
            "proposed_update": new_content,
            "timestamp": existing.get("timestamp", time.time()),
            "conflict": True,
            "metadata": existing.get("metadata", {}),
        }
        self._memories[f"{key}__conflict"] = entry
        self._save()
        logger.warning(f"Conflict flagged for '{key}'")
        return entry

    def get(self, key: str) -> Optional[dict]:
        return self._memories.get(key)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_lower = query.lower()
        results = []
        for key, entry in self._memories.items():
            if key.endswith("__conflict"):
                continue
            content_lower = entry.get("content", "").lower()
            if query_lower in content_lower or query_lower in key.lower():
                results.append(entry)
        return results[:top_k]

    def recall_relevant(self, query: str) -> dict:
        results = self.search(query)
        return {"deep_memories": results} if results else {}

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._memories:
                del self._memories[key]
                conflict_key = f"{key}__conflict"
                if conflict_key in self._memories:
                    del self._memories[conflict_key]
                self._save()
                return True
            return False

    def resolve_conflict(self, key: str, use_new: bool = False) -> bool:
        conflict_key = f"{key}__conflict"
        with self._lock:
            if conflict_key not in self._memories:
                return False
            conflict = self._memories[conflict_key]
            if use_new:
                self._memories[key] = {
                    "key": key,
                    "content": conflict.get("proposed_update", ""),
                    "timestamp": time.time(),
                    "mention_count": self._memories.get(key, {}).get("mention_count", 0) + 1,
                    "metadata": {},
                }
            del self._memories[conflict_key]
            self._save()
            return True

    def clear(self):
        with self._lock:
            self._memories.clear()
            self._save()

    def get_all(self) -> list[dict]:
        return [e for e in self._memories.values() if not e.get("key", "").endswith("__conflict")]

    def get_count(self) -> int:
        return len(self.get_all())

    def get_conflicts(self) -> list[dict]:
        return [e for e in self._memories.values() if e.get("key", "").endswith("__conflict")]

    def get_stats(self) -> dict:
        return {
            "permanent_count": self.get_count(),
            "conflict_count": len(self.get_conflicts()),
            "storage_path": str(self._storage_path),
        }
