import logging
import threading
import time
from typing import Optional

logger = logging.getLogger("iris.memory.orchestrator")


class MemoryOrchestrator:
    """
    Coordinates all three memory layers.
    Handles promotion/demotion between layers.
    """

    def __init__(self, temp_layer=None, long_temp_layer=None, deep_layer=None):
        self._temp = temp_layer
        self._long_temp = long_temp_layer
        self._deep = deep_layer
        self._lock = threading.Lock()
        self._promotion_lock = threading.Lock()
        logger.info("MemoryOrchestrator initialized")

    def set_layers(self, temp, long_temp, deep):
        self._temp = temp
        self._long_temp = long_temp
        self._deep = deep

    def store(self, key: str, content: str, permanent: bool = False, metadata: dict = None) -> dict:
        """
        Store a memory. Default goes to TempLayer.
        If permanent=True, goes directly to DeepLayer.
        """
        metadata = metadata or {}

        if permanent:
            if self._deep:
                return {"layer": "deep", **self._deep.store(key, content, metadata)}
            return {"error": "DeepLayer not available"}

        if self._temp:
            result = self._temp.store(key, content, metadata)
            if result.get("promoted") and self._long_temp:
                lt_result = self._long_temp.store(key, content, metadata)
                return {"layer": "long_temp", **lt_result}
            return {"layer": "temp", **result}

        return {"error": "No memory layer available"}

    def store_long(self, key: str, content: str, metadata: dict = None) -> dict:
        """Store directly in LongTempLayer (user said 'save it for a while')."""
        if self._long_temp:
            result = self._long_temp.store(key, content, metadata)
            return {"layer": "long_temp", **result}
        return {"error": "LongTempLayer not available"}

    def store_permanent(self, key: str, content: str, metadata: dict = None) -> dict:
        """Store directly in DeepLayer (user said 'remember forever')."""
        if self._deep:
            result = self._deep.store(key, content, metadata)
            return {"layer": "deep", **result}
        return {"error": "DeepLayer not available"}

    def recall_relevant(self, query: str) -> dict:
        """Search all three layers and merge results."""
        context = {}
        if self._temp:
            context.update(self._temp.recall_relevant(query))
        if self._long_temp:
            context.update(self._long_temp.recall_relevant(query))
        if self._deep:
            context.update(self._deep.recall_relevant(query))
        return context

    def get(self, key: str) -> Optional[dict]:
        for layer_name, layer in [("deep", self._deep), ("long_temp", self._long_temp), ("temp", self._temp)]:
            if layer:
                entry = layer.get(key)
                if entry:
                    entry["layer"] = layer_name
                    return entry
        return None

    def delete(self, key: str) -> bool:
        for layer in [self._deep, self._long_temp, self._temp]:
            if layer and layer.delete(key):
                return True
        return False

    def promote_to_deep(self, key: str) -> bool:
        """Manually promote a key from LongTemp to Deep."""
        if not self._long_temp or not self._deep:
            return False
        entry = self._long_temp.get(key)
        if not entry:
            return False
        self._deep.store(key, entry["content"], entry.get("metadata"))
        self._long_temp.delete(key)
        logger.info(f"Promoted '{key}' to deep memory")
        return True

    def run_maintenance(self):
        """Periodic cleanup — run on a timer."""
        if self._temp:
            self._temp._cleanup()
        logger.debug("Memory maintenance complete")

    def get_all(self) -> dict:
        return {
            "temp": self._temp.get_all() if self._temp else [],
            "long_temp": self._long_temp.get_all() if self._long_temp else [],
            "deep": self._deep.get_all() if self._deep else [],
        }

    def get_stats(self) -> dict:
        return {
            "temp_count": self._temp.get_count() if self._temp else 0,
            "long_temp_count": self._long_temp.get_count() if self._long_temp else 0,
            "deep_count": self._deep.get_count() if self._deep else 0,
        }

    def clear_all(self):
        if self._temp:
            self._temp.clear()
        if self._long_temp:
            self._long_temp.clear()
        if self._deep:
            self._deep.clear()
        logger.info("All memory layers cleared")
