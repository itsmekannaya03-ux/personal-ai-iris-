"""Context Engine — maintains conversation continuity."""


class ContextEngine:
    def __init__(self, max_tokens: int = 4096):
        self._max_tokens = max_tokens
        self._session_contexts: dict[str, dict] = {}

    def load(self, session_id: str, conversation_history: list) -> dict:
        session = self._session_contexts.get(session_id, {"topics": [], "facts": [], "last_topic": None})
        recent = conversation_history[-10:] if conversation_history else []
        return {
            "session_id": session_id,
            "current_topics": session.get("topics", []),
            "last_topic": session.get("last_topic"),
            "known_facts": session.get("facts", []),
            "recent_messages": recent,
            "message_count": len(conversation_history),
        }

    def update(self, session_id: str, user_message: str, ai_response: str, topic: str = None):
        if session_id not in self._session_contexts:
            self._session_contexts[session_id] = {"topics": [], "facts": [], "last_topic": None}
        session = self._session_contexts[session_id]
        if topic:
            session["last_topic"] = topic
            if topic not in session["topics"]:
                session["topics"].append(topic)
                if len(session["topics"]) > 20:
                    session["topics"] = session["topics"][-20:]

    def detect_topic_change(self, session_id: str, new_message: str) -> bool:
        session = self._session_contexts.get(session_id)
        if not session or not session.get("last_topic"):
            return False
        topic_keywords = {
            "coding": ["code", "function", "bug", "api", "app"],
            "writing": ["write", "draft", "edit", "essay", "email"],
            "research": ["research", "find", "search", "what is", "tell me about"],
            "system": ["open", "run", "execute", "setting"],
        }
        current_topic = session.get("last_topic", "")
        current_kw = topic_keywords.get(current_topic, [])
        new_kw = topic_keywords.get("research", [])
        matches_current = sum(1 for kw in current_kw if kw in new_message.lower())
        matches_new = sum(1 for kw in new_kw if kw in new_message.lower())
        return matches_new > matches_current and matches_current == 0

    def compress(self, conversation_history: list) -> str:
        if not conversation_history:
            return ""
        lines = [f"{m.get('role','?')}: {m.get('content','')[:100]}" for m in conversation_history[-20:]]
        return "\n".join(lines)

    def reset_session(self, session_id: str):
        self._session_contexts.pop(session_id, None)
