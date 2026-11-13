"""
MemorySummarizer — Distills conversation turns into concise summaries and key facts.

Compresses conversation history to prevent context overflow while preserving
decisions, user preferences, and actionable context.
"""

import logging
import re
from typing import Optional, List, Dict, Any, Callable

logger = logging.getLogger("iris.memory.summarizer")

FACT_EXTRACTION_PATTERNS = [
    r"(?:my name is|i am|call me)\s+([A-Za-z0-9_\-\s]+)",
    r"(?:i like|i love|i prefer|my favorite\s+\w+\s+is)\s+([A-Za-z0-9_\-\s]+)",
    r"(?:i live in|i am from|my location is)\s+([A-Za-z0-9_\-\s]+)",
    r"(?:i work as|my job is|i am a)\s+([A-Za-z0-9_\-\s]+)",
    r"(?:my goal is|i want to)\s+([A-Za-z0-9_\-\s]+)",
]


class MemorySummarizer:
    """
    Summarizes conversation logs and extracts notable facts.
    """

    def __init__(self, llm_generate_fn: Optional[Callable[[str, str], str]] = None):
        self._generate_fn = llm_generate_fn

    def set_generator(self, fn: Callable[[str, str], str]):
        self._generate_fn = fn

    def summarize_messages(self, messages: List[Dict[str, Any]], max_chars: int = 600) -> str:
        """Produce a concise summary of the given message list."""
        if not messages:
            return ""

        formatted_turns = []
        for m in messages[-30:]:
            role = m.get("role", "user").capitalize()
            content = m.get("content", "")
            if content:
                formatted_turns.append(f"{role}: {content[:150]}")

        transcript = "\n".join(formatted_turns)

        # 1. Try LLM generation if callback is wired
        if self._generate_fn:
            try:
                system_prompt = (
                    "You are a concise conversation summarizer. Distill the dialogue into 2-4 "
                    "bullet points capturing the user's goals, key facts mentioned, and current context. "
                    "Be extremely brief. No introductory text."
                )
                res = self._generate_fn(transcript, system_prompt)
                if res and len(res.strip()) > 10:
                    return res.strip()[:max_chars]
            except Exception as e:
                logger.warning(f"LLM summarization failed, using heuristic: {e}")

        # 2. Heuristic fallback summarizer
        return self._heuristic_summary(messages)

    def _heuristic_summary(self, messages: List[Dict[str, Any]]) -> str:
        user_queries = []
        key_facts = []

        for m in messages:
            if m.get("role") == "user":
                txt = m.get("content", "").strip()
                if txt:
                    user_queries.append(txt)
                    facts = self.extract_facts(txt)
                    key_facts.extend(facts)

        summary_points = []
        if key_facts:
            summary_points.append("User facts: " + "; ".join(list(dict.fromkeys(key_facts))[:3]))
        if user_queries:
            recent_topics = [q[:60] for q in user_queries[-3:]]
            summary_points.append("Recent topics: " + " | ".join(recent_topics))

        return "\n".join(f"- {p}" for p in summary_points) if summary_points else "Recent conversation focused on general inquiries."

    def extract_facts(self, text: str) -> List[str]:
        """Extract explicit user statements that should be candidates for permanent memory."""
        extracted = []
        t = text.strip()
        for patt in FACT_EXTRACTION_PATTERNS:
            matches = re.findall(patt, t, re.IGNORECASE)
            for m in matches:
                clean = m.strip().rstrip(".,!?")
                if len(clean) > 2:
                    extracted.append(clean)
        return extracted
