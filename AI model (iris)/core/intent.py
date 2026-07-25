import re
import logging

logger = logging.getLogger("igris.core.intent")


class IntentDetector:
    PATTERNS = {
        "greeting": r"\b(hello|hi|hey|good morning|good evening|good afternoon|yo|sup|what's up)\b",
        "farewell": r"\b(bye|goodbye|see you|talk later|good night|night)\b",
        "query": r"\b(who|what|when|where|why|how|tell me|explain|define|meaning of|what is|what are)\b",
        "launch": r"\b(open|launch|start|run)\s+\w+",
        "close_app": r"\b(close|exit|quit|kill)\s+\w+",
        "remember": r"\b(remember|save|store|note|note down|keep in mind)\b",
        "recall": r"\b(what.*remember|recall|what.*say|what.*tell|remind me)\b",
        "search": r"\b(search|google|look up|find|look for|browse)\b",
        "create": r"\b(create|make|write|draft|generate|build)\b",
        "system": r"\b(shutdown|restart|sleep|lock|log off|hibernate)\b",
        "delete": r"\b(delete|remove|erase|trash|get rid of)\b",
        "help": r"\b(help|what can you do|commands|capabilities)\b",
        "mode_switch": r"\b(mode|switch to|change mode)\b",
        "status_check": r"\b(status|how are you|what's your status|systems? check)\b",
        "confirm": r"\b(yes|yeah|yep|sure|go ahead|confirm|do it)\b",
        "deny": r"\b(no|nope|nah|cancel|stop|don't|abort)\b",
        "music": r"\b(play|pause|skip|music|song|playlist|album)\b",
        "message": r"\b(send|message|text|email|whatsapp|telegram)\b",
        "file_op": r"\b(move|copy|rename|list|show.*file|find.*file|organize)\b",
        "screenshot": r"\b(screenshot|screen capture|capture screen|print screen)\b",
        "web_nav": r"\b(go to|navigate|open website|visit)\b",
    }

    def __init__(self):
        self._compiled = {name: re.compile(patt, re.IGNORECASE) for name, patt in self.PATTERNS.items()}
        logger.info(f"IntentDetector ready ({len(self._compiled)} patterns)")

    def analyze(self, text: str) -> dict:
        text_lower = text.lower().strip()
        matches = {}
        for name, pattern in self._compiled.items():
            m = pattern.search(text_lower)
            if m:
                matches[name] = m.group()

        intent = self._resolve_intent(matches)
        confidence = self._calculate_confidence(matches)
        return {
            "intent": intent,
            "confidence": confidence,
            "matches": list(matches.keys()),
        }

    def _resolve_intent(self, matches: dict) -> str:
        priority = [
            "system", "delete", "mode_switch", "launch", "close_app",
            "message", "music", "web_nav", "screenshot", "file_op",
            "remember", "recall", "search", "create", "query",
            "confirm", "deny", "help", "status_check",
            "greeting", "farewell",
        ]
        for p in priority:
            if p in matches:
                return p
        return "conversation"

    def _calculate_confidence(self, matches: dict) -> float:
        if not matches:
            return 0.0
        total = len(matches)
        high_priority = sum(1 for m in matches if m in (
            "launch", "close_app", "system", "delete", "mode_switch",
            "remember", "music", "message", "web_nav", "screenshot"
        ))
        score = min(1.0, 0.3 + (total * 0.2) + (high_priority * 0.15))
        return round(score, 2)
