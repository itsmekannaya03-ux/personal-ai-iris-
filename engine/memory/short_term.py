"""
ShortTermMemory — Sliding conversation buffer with token-aware lifecycle.

Layer 1 of the IRIS 3-Tier Memory System.
Tracks recent conversation turns, estimates token usage, provides warning/critical ratios,
and prepares messages for prompt context or summarization triggers.
"""

import threading
import time
from datetime import datetime
from typing import Optional, List, Dict, Any


def estimate_tokens(text: str) -> int:
    """Fast approximation of token count (~4 characters per token)."""
    return max(1, len(text) // 4) if text else 0


class ShortTermMemory:
    """
    In-memory, thread-safe conversation buffer.
    Maintains a sliding window with token bounds and summary persistence.
    """

    DEFAULT_MAX_TOKENS = 4096
    NEAR_LIMIT_RATIO = 0.75
    AUTO_SUMMARIZE_RATIO = 0.90
    MAX_MESSAGES_CAP = 500

    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS):
        self.max_tokens = max(256, max_tokens)
        self._messages: List[Dict[str, Any]] = []
        self._summary: Optional[str] = None
        self._lock = threading.Lock()

    def add(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a new conversation turn."""
        content = content.strip() if content else ""
        msg = {
            "id": f"msg_{int(time.time() * 1000)}_{len(self._messages)}",
            "role": role,
            "content": content,
            "tokens": estimate_tokens(content) + estimate_tokens(role),
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        with self._lock:
            self._messages.append(msg)
            if len(self._messages) > self.MAX_MESSAGES_CAP:
                self._messages = self._messages[-self.MAX_MESSAGES_CAP:]
        return msg

    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return a copy of recent messages."""
        with self._lock:
            if limit:
                return list(self._messages[-limit:])
            return list(self._messages)

    def tokens_used(self) -> int:
        """Calculate total tokens consumed in the active session."""
        with self._lock:
            tokens = sum(m.get("tokens", 0) for m in self._messages)
            if self._summary:
                tokens += estimate_tokens(self._summary)
            return tokens

    def token_ratio(self) -> float:
        """Ratio of context window used (0.0 to 1.0)."""
        tokens = self.tokens_used()
        return min(1.0, tokens / self.max_tokens) if self.max_tokens else 0.0

    def needs_summarization(self) -> bool:
        """True if the token ratio exceeds the auto-summarize threshold."""
        return self.token_ratio() >= self.AUTO_SUMMARIZE_RATIO

    def is_near_limit(self) -> bool:
        """True if the token ratio exceeds the warning threshold."""
        return self.token_ratio() >= self.NEAR_LIMIT_RATIO

    def set_summary(self, summary: str):
        """Set the distilled summary of older conversation turns."""
        with self._lock:
            self._summary = summary.strip() if summary else None

    def get_summary(self) -> Optional[str]:
        """Get the active conversation summary."""
        with self._lock:
            return self._summary

    def get_context_history(self, max_turns: int = 10) -> str:
        """
        Format recent conversation turns and existing summary into a clean context string
        for prompt injection.
        """
        with self._lock:
            parts = []
            if self._summary:
                parts.append(f"[Previous Conversation Summary]\n{self._summary}\n")
            recent = self._messages[-max_turns:] if self._messages else []
            for msg in recent:
                role_label = "User" if msg["role"] == "user" else "Iris"
                parts.append(f"{role_label}: {msg['content']}")
            return "\n".join(parts)

    def new_session(self, keep_summary: bool = True) -> Dict[str, Any]:
        """Clear active messages to start a new session, optionally preserving the summary."""
        with self._lock:
            cleared_count = len(self._messages)
            if not keep_summary:
                self._summary = None
            self._messages = []
            return {
                "cleared_count": cleared_count,
                "summary": self._summary,
                "status": "Session reset successfully.",
            }

    def clear(self):
        """Hard reset of all messages and summary."""
        with self._lock:
            self._messages.clear()
            self._summary = None

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic metrics about current buffer usage."""
        with self._lock:
            used = sum(m.get("tokens", 0) for m in self._messages)
            if self._summary:
                used += estimate_tokens(self._summary)
            ratio = min(1.0, used / self.max_tokens) if self.max_tokens else 0.0

            if ratio >= self.AUTO_SUMMARIZE_RATIO:
                status_level = "critical"
                msg = "Context ceiling reached. Auto-summarization recommended."
            elif ratio >= self.NEAR_LIMIT_RATIO:
                status_level = "warning"
                msg = "Context nearing limit."
            else:
                status_level = "ok"
                msg = "Context is healthy."

            return {
                "tokens_used": used,
                "max_tokens": self.max_tokens,
                "ratio": round(ratio, 3),
                "status": status_level,
                "message": msg,
                "message_count": len(self._messages),
                "has_summary": bool(self._summary),
            }
