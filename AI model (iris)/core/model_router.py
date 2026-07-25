import logging
from typing import Optional

logger = logging.getLogger("igris.core.model_router")


class ModelRouter:
    """
    Routes requests to the appropriate AI model based on intent and mode.

    Simple intents (greeting, farewell) → lightweight model or rule-based
    Coding / analytical intents → deep reasoning model
    Default → general purpose model
    """

    def __init__(self, inference_engine=None, fallback=None):
        self._engine = inference_engine
        self._fallback = fallback or self._default_fallback

    def set_engine(self, engine):
        self._engine = engine

    def generate(self, prompt: str, intent: str = "unknown", context: dict = None, mode: str = "genius") -> str:
        context = context or {}
        system_prompt = self._build_system_prompt(intent, mode, context)

        if self._engine:
            try:
                params = {"max_tokens": 512 if mode == "fast" else 2048, "temperature": 0.3 if mode == "fast" else 0.7}
                if intent in ("greeting", "farewell"):
                    return self._fast_response(prompt, intent)
                return self._engine.generate(prompt, system_prompt=system_prompt)
            except Exception as e:
                logger.warning(f"Engine inference failed: {e}, falling back")
                return self._fallback(prompt)

        return self._fallback(prompt)

    def generate_stream(self, prompt: str, intent: str = "unknown", context: dict = None, mode: str = "genius"):
        context = context or {}
        system_prompt = self._build_system_prompt(intent, mode, context)

        if self._engine and hasattr(self._engine, 'generate_stream'):
            try:
                yield from self._engine.generate_stream(prompt, system_prompt=system_prompt)
            except Exception as e:
                logger.warning(f"Stream failed: {e}")
                yield self._fallback(prompt)
        else:
            yield self._fallback(prompt)

    def _build_system_prompt(self, intent: str, mode: str, context: dict) -> str:
        parts = [f"You are Iris, a professional AI assistant.", f"Mode: {mode}.", f"Intent: {intent}."]
        if mode == "fast":
            parts.append("Be concise. One or two sentences maximum.")
        else:
            parts.append("Provide thorough, well-reasoned responses.")
        if context:
            ctx_summary = "; ".join(f"{k}: {v}" for k, v in context.items() if isinstance(v, str))
            if ctx_summary:
                parts.append(f"Relevant context: {ctx_summary[:500]}")
        return " ".join(parts)

    def _fast_response(self, prompt: str, intent: str) -> str:
        responses = {
            "greeting": "Hello! How can I assist you today?",
            "farewell": "Goodbye. I'll be here when you need me.",
        }
        if intent in responses:
            return responses[intent]
        return f"Acknowledged: '{prompt[:100]}'."

    def _default_fallback(self, prompt: str) -> str:
        return f"I understand you said: '{prompt}'. For full capability, please connect a model backend."

    def get_status(self) -> dict:
        return {"engine_connected": self._engine is not None}
