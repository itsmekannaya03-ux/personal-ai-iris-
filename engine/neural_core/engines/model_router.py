"""Model Router — selects the best AI model for each task.

Routing logic:
Simple chat       → Qwen 3 / LLaMA 3.2
Code writing      → Qwen Coder 3
Code review       → Qwen Coder 2.5
Deep reasoning    → DeepSeek R1
Fast reply        → Gemma / LLaMA 3.2 3B
Research          → DeepSeek R1 / GLM
Long reasoning    → Kimi 2.6 / Nemotron 3
Offline mode      → LLaMA 3.2 3B
Cloud (PIE OK)    → Best available cloud
"""


TASK_MODEL_PREFERENCE = {
    "general": ["qwen3", "llama3.2", "gemma", "llama3.2-3b"],
    "coding": ["qwen-coder-3", "qwen-coder-2.5", "deepseek-coder", "llama3.2"],
    "code_review": ["qwen-coder-2.5", "qwen-coder-3", "llama3.2"],
    "reasoning": ["deepseek-r1", "kimi-2.6", "qwen3", "nemotron-3"],
    "fast": ["gemma", "llama3.2-3b", "phi-3"],
    "research": ["deepseek-r1", "glm", "kimi-2.6", "qwen3"],
    "long_reasoning": ["kimi-2.6", "nemotron-3", "deepseek-r1"],
    "offline": ["llama3.2-3b", "phi-3", "gemma"],
}


class ModelRouter:
    def __init__(self, model_manager):
        self._manager = model_manager
        self._fallback_chain = ["llama3.2", "llama3.2-3b", "gemma"]
        self._task_types = list(TASK_MODEL_PREFERENCE.keys())

    def select(self, task_type: str, available_models: list) -> str:
        preferences = TASK_MODEL_PREFERENCE.get(task_type, TASK_MODEL_PREFERENCE["general"])
        for model in preferences:
            if model in available_models:
                return model
        for model in self._fallback_chain:
            if model in available_models:
                return model
        return available_models[0] if available_models else "llama3.2-3b"

    def select_with_fallback(self, task_type: str, available_models: list) -> dict:
        primary = self.select(task_type, available_models)
        fallbacks = [m for m in self._fallback_chain if m != primary and m in available_models]
        return {
            "primary": primary,
            "fallbacks": fallbacks[:2],
            "emergency": self._fallback_chain[-1],
        }

    def detect_task_type(self, message: str, intent_label: str) -> str:
        if intent_label.startswith("intent_"):
            return self._manager.detect_task_type(message, intent_label) if hasattr(self._manager, 'detect_task_type') else "general"
        return self._manager.detect_task_type(message, intent_label) if hasattr(self._manager, 'detect_task_type') else "general"

    def task_type_from_message(self, message: str) -> str:
        coding_kw = ["code", "function", "bug", "debug", "implement", "class", "def "]
        reasoning_kw = ["why", "how", "explain", "analyze", "compare", "what if"]
        fast_kw = ["yes", "no", "ok", "thanks", "hello", "hi", "hey"]
        if any(kw in message.lower() for kw in coding_kw):
            return "coding"
        if any(kw in message.lower() for kw in reasoning_kw):
            return "reasoning"
        if len(message.split()) < 4 or any(kw in message.lower() for kw in fast_kw):
            return "fast"
        return "general"

    def get_preferred_models(self, task_type: str) -> list:
        return TASK_MODEL_PREFERENCE.get(task_type, TASK_MODEL_PREFERENCE["general"])

    def get_supported_tasks(self) -> list:
        return self._task_types
