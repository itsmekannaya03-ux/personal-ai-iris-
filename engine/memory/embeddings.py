"""
IGRIS Runtime — Memory Backend Abstraction

The memory system can be replaced without changing the core engine.
Default: MemoryManager (ChromaDB + JSON)
Alternatives: Redis, SQLite, PostgreSQL, in-memory-only
"""

from abc import ABC, abstractmethod
from typing import Optional


class MemoryBackend(ABC):
    @abstractmethod
    def store_short_term(self, role: str, content: str): pass

    @abstractmethod
    def store_long_term(self, text: str, weight: int = 1, **kwargs) -> bool: pass

    @abstractmethod
    def query_long_term(self, query: str, n_results: int = 5) -> list[dict]: pass

    @abstractmethod
    def get_deep_memories(self) -> list[str]: pass

    @abstractmethod
    def get_stats(self) -> dict: pass

    @abstractmethod
    def process_message(self, text: str) -> Optional[str]: pass

    @property
    @abstractmethod
    def backend_name(self) -> str: pass


_engine_instance: Optional[MemoryBackend] = None


def get_memory_backend() -> MemoryBackend:
    global _engine_instance
    if _engine_instance is None:
        from .memory_manager import MemoryManager
        _engine_instance = _MemoryAdapter(MemoryManager())
    return _engine_instance


class _MemoryAdapter(MemoryBackend):
    def __init__(self, inner):
        self._inner = inner

    @property
    def backend_name(self) -> str:
        return "Default (ChromaDB + JSON)"

    def store_short_term(self, role: str, content: str):
        self._inner.store_short_term(role, content)

    def store_long_term(self, text: str, weight: int = 1, **kwargs) -> bool:
        return self._inner.store_long_term(text, weight, **kwargs)

    def query_long_term(self, query: str, n_results: int = 5) -> list[dict]:
        return self._inner.query_long_term(query, n_results)

    def get_deep_memories(self) -> list[str]:
        return self._inner.get_deep_memories()

    def get_stats(self) -> dict:
        return self._inner.get_stats()

    def process_message(self, text: str) -> Optional[str]:
        return self._inner.process_message(text)
