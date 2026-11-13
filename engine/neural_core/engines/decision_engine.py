"""Decision Engine — makes final decisions when ambiguity exists."""


class DecisionEngine:
    def __init__(self):
        self._rules = {
            "privacy_over_performance": True,
            "ask_if_uncertain": True,
            "confidence_threshold": 0.6,
        }

    def choose_model(self, task_type: str, available_models: list, ram_available_mb: int) -> str:
        preferences = {
            "general": ["qwen3", "llama3.2", "gemma"],
            "coding": ["qwen-coder-3", "qwen-coder-2.5", "llama3.2"],
            "reasoning": ["deepseek-r1", "kimi-2.6", "qwen3"],
            "fast": ["gemma", "llama3.2-3b"],
            "research": ["deepseek-r1", "glm"],
        }
        preferred = preferences.get(task_type, ["llama3.2"])
        for model in preferred:
            if model in available_models:
                return model
        return available_models[0] if available_models else "llama3.2-3b"

    def choose_local_or_cloud(self, pie_decision: str, privacy_mode: str, user_preference: str = None) -> str:
        if user_preference == "local":
            return "local"
        if privacy_mode == "strict":
            return "local"
        if pie_decision == "blocked":
            return "local"
        if pie_decision == "cloud_allowed" and privacy_mode != "strict":
            return "cloud"
        return "local"

    def ask_for_clarification(self, confidence: float, text: str) -> bool:
        return confidence < self._rules["confidence_threshold"]

    def how_to_format(self, intent: str, mode: str) -> str:
        if mode == "focus":
            return "concise"
        if mode == "friend":
            return "conversational"
        if intent in ("coding", "technical"):
            return "detailed"
        return "balanced"

    def should_activate_plugin(self, plugin_id: str, user_enabled_plugins: list) -> bool:
        return plugin_id in user_enabled_plugins

    def handle_error(self, error_type: str, retry_count: int) -> str:
        if retry_count < 3:
            return "retry"
        if error_type in ("model_crash", "memory_error"):
            return "fallback"
        return "notify_user"

    def set_rule(self, rule: str, value: bool):
        if rule in self._rules:
            self._rules[rule] = value
