import time
import logging
from pathlib import Path
from typing import Optional
from memory.db import DatabaseManager

logger = logging.getLogger("iris.memory.temp")

class TempLayer:
    """
    Short-term memory — lives 48 hours, then auto-deleted.
    If reinforced (same topic mentioned again within 48h), becomes
    eligible for promotion to LongTempLayer.
    """

    TTL = 48 * 3600

    def __init__(self, storage_path: Optional[str] = None):
        self.db = DatabaseManager(storage_path)
        logger.info(f"TempLayer ready ({self.get_count()} items)")

    def _cleanup(self):
        try:
            self.db.purge_expired_temp(self.TTL)
        except Exception as e:
            logger.error(f"Failed to clean temp memories: {e}")

    def store(self, key: str, content: str, metadata: dict = None) -> dict:
        now = time.time()
        self._cleanup() # Clean before storing
        r = self.db.store_temp(key, content, now, metadata or {})
        promoted = r["mention_count"] >= 2
        entry = self.db.get_entry("temp", key)
        return {"entry": entry, "promoted": promoted}

    def get(self, key: str) -> Optional[dict]:
        self._cleanup()
        return self.db.get_entry("temp", key)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        self._cleanup()
        results = self.db.search_layer("temp", query, ttl=self.TTL)
        return results[:top_k]

    def recall_relevant(self, query: str) -> dict:
        results = self.search(query)
        return {"temp_memories": results} if results else {}

    def delete(self, key: str) -> bool:
        return self.db.delete_entry("temp", key)

    def clear(self):
        self.db.clear_layer("temp")

    def get_all(self) -> list[dict]:
        self._cleanup()
        return self.db.get_all_entries("temp", ttl=self.TTL)

    def get_count(self) -> int:
        self._cleanup()
        return self.db.get_count("temp", ttl=self.TTL)

    def get_stats(self) -> dict:
        return {"active_count": self.get_count(), "db_path": self.db.db_path, "ttl_hours": 48}
