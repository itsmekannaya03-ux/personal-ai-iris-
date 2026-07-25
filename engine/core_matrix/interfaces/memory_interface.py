"""Memory Interface — connects Neural Core to Memory Engine."""


class MemoryInterface:
    def __init__(self, memory_manager):
        self._memory = memory_manager

    def read_short_term(self, session_id: str, limit: int = 20) -> list:
        return getattr(self._memory, 'short_term', [])[-limit:]

    def read_long_term(self, query: str, top_k: int = 5) -> list:
        try:
            return self._memory.query_long_term(query)[:top_k]
        except Exception:
            return []

    def read_deep(self) -> list:
        try:
            return self._memory.get_deep_memories()
        except Exception:
            return []

    def write(self, tier: str, role: str, content: str, pie_clearance: str = "approved"):
        if pie_clearance == "blocked":
            return {"status": "blocked", "reason": "PIE denied"}
        try:
            if tier == "short":
                self._memory.store_short_term(role, content)
            elif tier == "long":
                self._memory.store_long_term(role, content)
            elif tier == "deep":
                self._memory.store_deep(content)
            return {"status": "success", "tier": tier}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def delete(self, memory_id: str, user_confirmed: bool = False) -> dict:
        if not user_confirmed:
            return {"status": "blocked", "reason": "User confirmation required"}
        return {"status": "success", "deleted": memory_id}

    def promote(self, content: str) -> dict:
        try:
            promoted = self._memory.process_message(content)
            return {"status": "success" if promoted else "no_change", "promoted": promoted}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def search(self, query: str, tier: str = "all") -> list:
        results = []
        if tier in ("all", "short"):
            results.extend(self.read_short_term("default"))
        if tier in ("all", "long"):
            results.extend(self.read_long_term(query))
        if tier in ("all", "deep"):
            results.extend(self.read_deep())
        return results

    def get_stats(self) -> dict:
        try:
            return self._memory.get_stats()
        except Exception:
            return {"short_term": 0, "long_term": 0, "deep": 0}
