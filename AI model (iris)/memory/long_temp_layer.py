import json
import time
import logging
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger("igris.memory.long_temp")


class LongTempLayer:
    """
    Medium-term memory — lives 2-3 weeks.
    Entries arrive via promotion from TempLayer or explicit user request.
    If reinforced repeatedly, becomes eligible for promotion to DeepLayer.
    """

    TTL = 18 * 24 * 3600
    REINFORCEMENT_THRESHOLD = 3

    def __init__(self, storage_path: Optional[str] = None):
        self._storage_path = Path(storage_path or self._default_path())
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._memories: dict[str, dict] = {}
        self._load()
        logger.info(f"LongTempLayer ready ({len(self._memories)} items)")

    def _default_path(self) -> str:
        return str(Path.home() / ".igris" / "memory_long_temp.json")

    def _load(self):
        try:
            if self._storage_path.exists():
                with open(self._storage_path) as f:
                    self._memories = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load long-temp memory: {e}")
            self._memories = {}

    def _save(self):
        try:
            self._storage_path.write_text(json.dumps(self._memories, indent=2))
        except Exception as e:
            logger.error(f"Failed to save long-temp memory: {e}")

    def store(self, key: str, content: str, metadata: dict = None) -> dict:
        with self._lock:
            now = time.time()
            existing = self._memories.get(key)
            mention_count = (existing.get("mention_count", 0) + 1) if existing else 1
            first_seen = existing.get("first_seen", now) if existing else now
            entry = {
                "key": key,
                "content": content,
                "first_seen": first_seen,
                "timestamp": now,
                "mention_count": mention_count,
                "metadata": metadata or {},
            }
            self._memories[key] = entry
            self._save()
            promoted = mention_count >= self.REINFORCEMENT_THRESHOLD
            return {"entry": entry, "promoted": promoted}

    def get(self, key: str) -> Optional[dict]:
        entry = self._memories.get(key)
        if entry and time.time() - entry.get("timestamp", 0) <= self.TTL:
            return entry
        return None

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_lower = query.lower()
        results = []
        now = time.time()
        for key, entry in self._memories.items():
            if now - entry.get("timestamp", 0) > self.TTL:
                continue
            content_lower = entry.get("content", "").lower()
            if query_lower in content_lower or query_lower in key.lower():
                results.append(entry)
        results.sort(key=lambda x: x.get("mention_count", 0), reverse=True)
        return results[:top_k]

    def recall_relevant(self, query: str) -> dict:
        results = self.search(query)
        return {"long_temp_memories": results} if results else {}

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._memories:
                del self._memories[key]
                self._save()
                return True
            return False

    def clear(self):
        with self._lock:
            self._memories.clear()
            self._save()

    def get_all(self) -> list[dict]:
        now = time.time()
        return [e for e in self._memories.values() if now - e.get("timestamp", 0) <= self.TTL]

    def get_count(self) -> int:
        return len(self.get_all())

    def get_stats(self) -> dict:
        return {"active_count": self.get_count(), "storage_path": str(self._storage_path), "ttl_days": 18}
