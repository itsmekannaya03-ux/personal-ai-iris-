"""Reasoning Engine — handles complex thinking tasks."""


class ReasoningEngine:
    def __init__(self):
        self._active = False

    def should_activate(self, message: str, intent: str) -> bool:
        keywords = ["why", "how", "explain", "reason", "analyze", "compare",
                     "what if", "implications", "cause", "effect", "prove"]
        if intent in ("deep_reasoning", "research"):
            return True
        return any(kw in message.lower() for kw in keywords)

    def reason(self, message: str, context: list = None) -> dict:
        self._active = True
        steps = [
            {"step": 1, "action": "Parse problem", "status": "complete"},
            {"step": 2, "action": "Break into sub-problems", "status": "complete"},
            {"step": 3, "action": "Reason through each step", "status": "pending"},
            {"step": 4, "action": "Connect steps logically", "status": "pending"},
            {"step": 5, "action": "Produce reasoned answer", "status": "pending"},
        ]
        return {
            "activated": True,
            "type": "reasoning",
            "steps": steps,
            "requires_deep_model": True,
            "suggested_model": "deepseek-r1",
        }

    @property
    def is_active(self) -> bool:
        return self._active
