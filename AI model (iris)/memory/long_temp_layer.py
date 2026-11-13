import time
import logging
from typing import Optional
from memory.db import DatabaseManager

logger = logging.getLogger("iris.memory.long_temp")

class LongTempLayer:
    """
    Medium-term memory — lives 18 days (2-3 weeks).
    Entries arrive via promotion from TempLayer or explicit user request.
    If reinforced repeatedly, becomes eligible for promotion to DeepLayer.
    """

    TTL = 18 * 24 * 3600
    REINFORCEMENT_THRESHOLD = 3

    def __init__(self, storage_path: Optional[str] = None):
        self.db = DatabaseManager(storage_path)
        logger.info(f"LongTempLayer ready ({self.get_count()} items)")

    def store(self, key: str, content: str, metadata: dict = None) -> dict:
        now = time.time()
        r = self.db.store_long_temp(key, content, now, metadata or {})
        promoted = r["mention_count"] >= self.REINFORCEMENT_THRESHOLD
        entry = self.db.get_entry("long_temp", key)
        return {"entry": entry, "promoted": promoted}

    def get(self, key: str) -> Optional[dict]:
        return self.db.get_entry("long_temp", key)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        results = self.db.search_layer("long_temp", query, ttl=self.TTL)
        return results[:top_k]

    def recall_relevant(self, query: str) -> dict:
        results = self.search(query)
        return {"long_temp_memories": results} if results else {}

    def delete(self, key: str) -> bool:
        return self.db.delete_entry("long_temp", key)

    def clear(self):
        self.db.clear_layer("long_temp")

    def get_all(self) -> list[dict]:
        return self.db.get_all_entries("long_temp", ttl=self.TTL)

    def get_count(self) -> int:
        return self.db.get_count("long_temp", ttl=self.TTL)

    def get_stats(self) -> dict:
        return {"active_count": self.get_count(), "db_path": self.db.db_path, "ttl_days": 18}
