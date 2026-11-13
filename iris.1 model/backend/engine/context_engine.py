"""
ContextEngine — Conversation context and token management.

Manages:
  - Conversation history with token counting
  - Token limits and auto-summarization
  - Context window management
  - Session state
"""

import time
import logging
import threading
from typing import Optional
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger("iris.context")


@dataclass
class Message:
    role: str  # user, assistant, system
    content: str
    timestamp: float = field(default_factory=time.time)
    tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "tokens": self.tokens,
        }


class ContextEngine:
    """
    Manages conversation context. Keeps track of history,
    enforces token limits, and auto-summarizes when needed.
    """

    DEFAULT_MAX_TOKENS = 4096
    SUMMARIZE_RATIO = 0.85
    TOKEN_ESTIMATE_RATIO = 4.0  # ~4 chars per token

    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS):
        self.max_tokens = max_tokens
        self._messages: deque[Message] = deque()
        self._system_prompt: Optional[str] = None
        self._context_summary: Optional[str] = None
        self._token_count = 0
        self._lock = threading.Lock()
        self._session_id = str(int(time.time()))
        logger.info(f"Context engine initialized (max_tokens={max_tokens})")

    def _estimate_tokens(self, text: str) -> int:
        return int(len(text) / self.TOKEN_ESTIMATE_RATIO) + 1

    def set_system_prompt(self, prompt: str):
        self._system_prompt = prompt
        logger.debug("System prompt updated")

    def add_message(self, role: str, content: str) -> Message:
        tokens = self._estimate_tokens(content)
        msg = Message(role=role, content=content, tokens=tokens)

        with self._lock:
            self._messages.append(msg)
            self._token_count += tokens
            self._check_token_limit()

        return msg

    def _check_token_limit(self):
        if self._token_count > int(self.max_tokens * self.SUMMARIZE_RATIO):
            logger.info(f"Token limit approaching ({self._token_count}/{self.max_tokens}), summarizing...")
            self._summarize_context()

    def _summarize_context(self):
        """Summarize old messages to free token space."""
        if len(self._messages) < 4:
            return

        old_messages = list(self._messages)[:-2]
        recent_messages = list(self._messages)[-2:]

        summary_parts = []
        for msg in old_messages:
            content = msg.content[:100]
            summary_parts.append(f"[{msg.role}]: {content}")

        summary = "Previous conversation summary:\n" + "\n".join(summary_parts)
        summary_tokens = self._estimate_tokens(summary)

        with self._lock:
            self._messages.clear()
            summary_msg = Message(role="system", content=summary, tokens=summary_tokens)
            self._messages.append(summary_msg)
            for msg in recent_messages:
                self._messages.append(msg)
            self._token_count = sum(m.tokens for m in self._messages)
            self._context_summary = summary

        logger.info(f"Context summarized: {len(old_messages)} messages compressed")

    def get_history(self, max_messages: Optional[int] = None) -> list[dict]:
        with self._lock:
            msgs = list(self._messages)
            if max_messages:
                msgs = msgs[-max_messages:]
            return [m.to_dict() for m in msgs]

    def get_context(self) -> list[dict]:
        """Get full context (system prompt + history) for model input."""
        context = []
        if self._system_prompt:
            context.append({"role": "system", "content": self._system_prompt})
        context.extend(self.get_history())
        return context

    def get_token_usage(self) -> dict:
        with self._lock:
            return {
                "current": self._token_count,
                "max": self.max_tokens,
                "usage_ratio": round(self._token_count / self.max_tokens, 2),
                "message_count": len(self._messages),
            }

    def clear(self):
        with self._lock:
            self._messages.clear()
            self._token_count = 0
            self._context_summary = None
        logger.info("Context cleared")

    def reset_session(self):
        self._session_id = str(int(time.time()))
        self.clear()
        logger.info(f"New session started: {self._session_id}")

    def get_session_id(self) -> str:
        return self._session_id

    def get_status(self) -> dict:
        return {
            "session_id": self._session_id,
            "token_usage": self.get_token_usage(),
            "has_system_prompt": self._system_prompt is not None,
            "has_summary": self._context_summary is not None,
            "message_count": len(self._messages),
        }
