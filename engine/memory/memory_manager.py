"""
MemoryManager — Unified Orchestrator for the IRIS 3-Tier Memory System.

Coordinates:
  - ShortTermMemory (sliding buffer + token management + auto-summarize)
  - LongTermMemory  (ChromaDB semantic vectors + JSON fallback + repetition weighting)
  - DeepMemory      (Fernet encrypted permanent facts & preferences)
  - MemorySummarizer (conversation distillations & heuristic fact extractor)

Handles the automatic promotion pipeline:
  Explicit declarations ("always remember") -> Deep Memory
  Conversation turns -> Short-Term Memory
  Repetitions (weight >= threshold) -> Promoted from Long-Term to Deep Memory
"""

import logging
import re
from typing import Optional, List, Dict, Any, Union

from .short_term import ShortTermMemory
from .long_term import LongTermMemory, MEMORY_TYPE_SEMANTIC, MEMORY_TYPE_EPISODIC, MEMORY_TYPE_PROCEDURAL
from .deep_memory import DeepMemory
from .summarizer import MemorySummarizer

logger = logging.getLogger("iris.memory.manager")

INSTANT_PROMOTION_KEYWORDS = [
    "always remember", "never forget", "remember this", "keep in mind forever",
    "permanently remember", "remember that",
]


class MemoryManager:
    """
    Main memory orchestrator for IRIS AI.
    Exposes unified methods for storing, querying, summarizing, and promoting memories.
    """

    def __init__(self, max_short_term_tokens: int = 4096, promotion_threshold: int = 5):
        self.short_term_store = ShortTermMemory(max_tokens=max_short_term_tokens)
        self.long_term_store = LongTermMemory(promotion_threshold=promotion_threshold)
        self.deep_memory_store = DeepMemory()
        self.summarizer = MemorySummarizer()

    # ── Short-Term Compatibility Properties ──────────────────────────

    @property
    def short_term(self) -> List[Dict[str, Any]]:
        return self.short_term_store.get_messages()

    @property
    def deep_memory(self) -> Dict[str, Any]:
        return {
            "memories": self.deep_memory_store.get_all_memories(),
            "facts": self.deep_memory_store.get_all_facts(),
        }

    @property
    def chroma(self):
        return self.long_term_store.chroma

    # ── Core Operations ──────────────────────────────────────────────

    def store_short_term(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Record a turn into short term memory."""
        self.short_term_store.add(role, content, metadata)

    def store_long_term(
        self,
        text: str,
        weight: int = 1,
        memory_type: str = MEMORY_TYPE_SEMANTIC,
        privacy_level: str = "medium",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Store a semantic memory into LongTermMemory.
        If the memory's repetition weight hits the promotion threshold,
        it is automatically promoted to DeepMemory and cleared from LongTerm.
        """
        should_promote, cur_weight = self.long_term_store.store(
            text=text,
            weight=weight,
            memory_type=memory_type,
            privacy_level=privacy_level,
            metadata=metadata,
        )
        if should_promote:
            self.deep_memory_store.remember(text, category="promoted")
            self.long_term_store.delete_by_text(text)
            logger.info(f"Memory promoted to Deep Store: '{text[:80]}'")
            return True
        return False

    def store_deep(self, text: str, category: str = "general") -> bool:
        """Store directly into encrypted Deep Memory."""
        return self.deep_memory_store.remember(text, category=category)

    def process_message(self, text: str) -> Optional[str]:
        """
        Analyze incoming user message for explicit memory commands or natural promotion.
        Returns the promoted fact text if a promotion occurred, otherwise None.
        """
        text_lower = text.lower()

        # 1. Instant explicit promotion
        for kw in INSTANT_PROMOTION_KEYWORDS:
            if kw in text_lower:
                idx = text_lower.index(kw) + len(kw)
                to_remember = text[idx:].strip().strip(".:\"'")
                # Clean leading prepositions
                to_remember = re.sub(r"^(that|to|about)\s+", "", to_remember, flags=re.IGNORECASE).strip()
                if to_remember:
                    self.deep_memory_store.remember(to_remember, category="user_assertion")
                    return to_remember

        # 2. Extract facts if any strong declaration
        facts = self.summarizer.extract_facts(text)
        for fact in facts:
            self.store_long_term(fact, weight=2)

        # 3. Standard storage into long-term memory
        promoted = self.store_long_term(text, weight=1)
        if promoted:
            return text
        return None

    def query_long_term(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search long term vector storage."""
        return self.long_term_store.query(query, n_results=n_results)

    def query_deep(self, query: str) -> List[str]:
        """Search encrypted deep memory."""
        return self.deep_memory_store.search(query)

    def recall_relevant(self, query: str) -> Dict[str, Any]:
        """Search all 3 tiers and merge relevant context for inference."""
        deep_matches = self.query_deep(query)
        long_matches = self.query_long_term(query, n_results=5)
        context_history = self.short_term_store.get_context_history(max_turns=6)

        return {
            "deep_memories": deep_matches,
            "long_term_memories": [m["text"] for m in long_matches],
            "context_history": context_history,
            "facts": self.deep_memory_store.get_all_facts(),
        }

    def get_deep_memories(self) -> List[str]:
        return self.deep_memory_store.get_all_memories()

    def get_long_term_summary(self) -> str:
        all_memories = self.long_term_store.get_all()
        if not all_memories:
            return "No long-term memories yet."
        lines = []
        for m in all_memories:
            txt = m.get("text", "")
            meta = m.get("metadata", {})
            w = meta.get("weight", 1)
            lines.append(f"[W:{w}] {txt[:100]}")
        return "\n".join(lines)

    def auto_summarize_if_needed(self) -> Optional[str]:
        """Trigger summarization if short term memory exceeds ceiling."""
        if self.short_term_store.needs_summarization():
            msgs = self.short_term_store.get_messages()
            summary = self.summarizer.summarize_messages(msgs)
            self.short_term_store.new_session(keep_summary=False)
            self.short_term_store.set_summary(summary)
            return summary
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Diagnostic summary across all 3 tiers."""
        return {
            "short_term": len(self.short_term_store.get_messages()),
            "long_term": self.long_term_store.get_count(),
            "deep": self.deep_memory_store.get_count(),
            "short_term_tokens": self.short_term_store.tokens_used(),
            "encrypted": self.deep_memory_store.is_encrypted(),
        }

    def clear_all(self):
        """Hard reset across all memory layers."""
        self.short_term_store.clear()
        self.long_term_store.clear()
        self.deep_memory_store.clear()
        logger.info("All 3 memory tiers cleared.")
