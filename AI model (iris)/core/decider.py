import logging
from typing import Optional

logger = logging.getLogger("igris.core.decider")


class Decider:
    """
    Decides whether IGRIS should reply, perform an action, or both.
    Routes actions to hands/ and replies to voice/.
    """

    REPLY_ONLY = {"greeting", "farewell", "conversation", "query", "help", "status_check", "confirm", "deny"}
    ACTION_ONLY = {"launch", "close_app", "system", "delete", "screenshot", "music", "message"}
    BOTH = {"search", "create", "file_op", "web_nav", "remember", "recall", "mode_switch"}

    def __init__(self):
        self._hands: Optional[object] = None

    def set_hands(self, hands):
        self._hands = hands

    def decide(self, data: dict) -> object:
        from .brain import Action

        intent = data.get("intent", "unknown")
        response_text = data.get("response", "")
        text = data.get("text", "")

        if intent in self.REPLY_ONLY:
            return Action(type="respond", payload={"text": response_text}, priority=0)

        if intent in self.ACTION_ONLY:
            execution = self._build_execution(intent, text) if self._hands else {}
            return Action(
                type="execute",
                payload={"text": response_text, "execution": execution},
                priority=1,
                requires_confirmation=self._needs_confirmation(intent),
            )

        if intent in self.BOTH:
            execution = self._build_execution(intent, text) if self._hands else {}
            return Action(
                type="both",
                payload={"text": response_text, "execution": execution},
                priority=1,
                requires_confirmation=self._needs_confirmation(intent),
            )

        return Action(type="respond", payload={"text": response_text}, priority=0)

    def _build_execution(self, intent: str, text: str) -> dict:
        return {
            "intent": intent,
            "source_text": text,
            "target": self._extract_target(intent, text),
        }

    def _extract_target(self, intent: str, text: str) -> str:
        import re
        if intent in ("launch", "close_app"):
            m = re.search(r"(?:open|launch|start|run|close|exit|quit|kill)\s+(\w[\w\s]*)", text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        if intent == "search":
            m = re.search(r"(?:search|google|look up|find)\s+(.+?)$", text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        if intent == "web_nav":
            m = re.search(r"(?:go to|navigate|open website|visit)\s+(.+?)$", text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        if intent == "music":
            m = re.search(r"(?:play|search)\s+(.+?)$", text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return text

    def _needs_confirmation(self, intent: str) -> bool:
        return intent in {"system", "delete", "close_app", "message"}

    def get_supported_intents(self) -> dict:
        return {
            "reply_only": list(self.REPLY_ONLY),
            "action_only": list(self.ACTION_ONLY),
            "both": list(self.BOTH),
        }
