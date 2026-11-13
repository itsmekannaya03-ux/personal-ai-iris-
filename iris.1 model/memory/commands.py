import re
import logging

logger = logging.getLogger("iris.memory.commands")


class MemoryCommands:
    """
    Handles explicit user commands for memory operations:
    - "remember that X" → store in TempLayer
    - "save it long" / "remember this for a while" → LongTempLayer
    - "remember this forever" / "never forget" → DeepLayer directly
    - "what do you remember about X" → recall across all layers
    - "forget X" / "delete memory of X" → delete from all layers
    """

    def __init__(self, orchestrator=None):
        self._orchestrator = orchestrator

    def set_orchestrator(self, orchestrator):
        self._orchestrator = orchestrator

    def parse(self, text: str) -> dict:
        """Parse a user message for memory commands and execute them."""
        text_lower = text.lower().strip()

        # "remember this forever" / "never forget" → Deep
        if re.search(r"(remember\s+this\s+forever|never\s+forget|always\s+remember|save\s+it\s+forever)", text_lower):
            content = self._extract_content(text, r"(?:remember this forever|never forget|always remember|save it forever)\s*(.*)", "that")
            if content:
                return self._store("permanent", content, text)
            return {"action": "error", "message": "What should I remember forever?"}

        # "save it long" / "remember this for a while" → LongTemp
        if re.search(r"(save\s+it\s+long|remember\s+this\s+for\s+a\s+while|keep\s+this\s+for\s+now)", text_lower):
            content = self._extract_content(text, r"(?:save it long|remember this for a while|keep this for now)\s*(.*)", "that")
            if content:
                return self._store("long", content, text)
            return {"action": "error", "message": "What should I save for later?"}

        # "remember that X" / "note that X" → Temp
        if re.search(r"\b(remember\s+that|remember|note\s+that|note\s+down|save\s+that|keep\s+in\s+mind)\b", text_lower):
            content = self._extract_content(text, r"(?:remember that|remember|note that|note down|save that|keep in mind)\s*(.*)", "")
            if content:
                return self._store("temp", content, text)
            return {"action": "error", "message": "What should I remember?"}

        # "what do you remember about X" / "recall X" / "remind me about X"
        if re.search(r"(what\s+do\s+you\s+remember|recall|remind\s+me|what.*about)", text_lower):
            query = self._extract_content(text, r"(?:what do you remember about|recall|remind me about|what.*about)\s*(.*)", "")
            if query:
                return self._recall(query)
            return self._recall(text)

        # "forget X" / "delete memory of X"
        if re.search(r"\b(forget|delete\s+memory|erase|remove\s+from\s+memory)\b", text_lower):
            key = self._extract_content(text, r"(?:forget|delete memory of|erase|remove from memory)\s*(.*)", "")
            if key:
                return self._forget(key)
            return {"action": "error", "message": "What should I forget?"}

        return {"action": None}

    def _extract_content(self, text: str, pattern: str, fallback: str) -> str:
        m = re.search(pattern, text, re.IGNORECASE)
        if m and m.group(1).strip():
            return m.group(1).strip()
        if fallback:
            m = re.search(rf"(?:{fallback})\s+(.+?)$", text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""

    def _store(self, layer: str, content: str, original: str) -> dict:
        if not self._orchestrator:
            return {"action": "error", "message": "Memory system not available."}
        key = content[:50].lower().replace(" ", "_").replace("'", "")
        if layer == "permanent":
            self._orchestrator.store_permanent(key, content)
            msg = f"I'll remember that permanently: {content}"
        elif layer == "long":
            self._orchestrator.store_long(key, content)
            msg = f"Saved for later: {content}"
        else:
            self._orchestrator.store(key, content)
            msg = f"Noted: {content}"
        return {"action": "stored", "message": msg, "key": key, "layer": layer}

    def _recall(self, query: str) -> dict:
        if not self._orchestrator:
            return {"action": "error", "message": "Memory system not available."}
        context = self._orchestrator.recall_relevant(query)
        memories = []
        for layer_key in ("temp_memories", "long_temp_memories", "deep_memories"):
            for m in context.get(layer_key, []):
                memories.append(f"{m.get('content', '')}")
        if memories:
            return {"action": "recalled", "message": "Here's what I remember: " + " | ".join(memories), "memories": memories}
        return {"action": "recalled", "message": "I don't have any memories about that.", "memories": []}

    def _forget(self, key: str) -> dict:
        if not self._orchestrator:
            return {"action": "error", "message": "Memory system not available."}
        deleted = self._orchestrator.delete(key.lower().replace(" ", "_"))
        if deleted:
            return {"action": "forgotten", "message": f"Forgotten: {key}"}
        return {"action": "error", "message": f"I couldn't find any memory about: {key}"}
