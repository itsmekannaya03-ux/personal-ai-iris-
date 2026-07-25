"""
IGRIS Runtime — Inference Engine Abstraction

This module is the ONLY place in IGRIS that knows about specific inference
backends. Everything else talks to the abstract InferenceEngine interface.

Currently supported:
  - OllamaEngine  (default, production)

Future engines (drop-in replacements, zero changes to ai.py):
  - LlamaCppEngine
  - IGRISFoundationEngine (custom IGRIS M1/M2 model)
  - HybridCloudEngine (routes through PIE)
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger("igris.runtime.inference")


# ─────────────────────────────────────────────────────────────────────────────
# Abstract Base
# ─────────────────────────────────────────────────────────────────────────────

class InferenceEngine(ABC):
    """
    The common contract all inference engines must implement.

    By depending on this interface—not on 'ollama' or any specific
    library—every other module in IGRIS can swap the inference engine
    at runtime without knowing the difference.
    """

    @abstractmethod
    def chat(self, model: str, messages: list[dict]) -> str:
        """
        Send a list of messages to the model and return the reply as a string.

        Args:
            model: The model identifier (e.g., 'llama3.2:3b', 'qwen2.5-coder:7b')
            messages: OpenAI-style message list [{"role": ..., "content": ...}]

        Returns:
            The assistant's reply as a plain string.
        """

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return a list of available model identifiers on this engine."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this engine is reachable and ready to serve requests."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Human-readable name, e.g. 'Ollama', 'llama.cpp', 'IGRIS M1'"""


# ─────────────────────────────────────────────────────────────────────────────
# Production Engine: Ollama (hidden implementation detail)
# ─────────────────────────────────────────────────────────────────────────────

class OllamaEngine(InferenceEngine):
    """
    Wraps the 'ollama' library.  This is the ONLY file in the entire IGRIS
    codebase that is allowed to import 'ollama'.

    Why Ollama as default:
      - Best local inference UX (one-command install, model downloads)
      - Large model catalogue
      - OpenAI-compatible API (easy to port off)

    Limitation:
      - Requires the Ollama binary to be running as a separate process.
        IGRIS OS will eventually manage this process lifecycle itself.
    """

    def __init__(self, host: str = "http://localhost:11434"):
        self._host = host
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            import ollama
            # ollama 0.x: use module-level functions
            # ollama 1.x+: use Client(host=...)
            try:
                self._client = ollama.Client(host=self._host)
                logger.info(f"[Runtime] OllamaEngine initialised with Client (host={self._host})")
            except AttributeError:
                # Older ollama SDK — module-level calls only
                self._client = None
                self._ollama_module = ollama
                logger.info("[Runtime] OllamaEngine initialised (module-level, legacy SDK)")
        except ImportError:
            logger.warning("[Runtime] 'ollama' package not installed. OllamaEngine unavailable.")

    @property
    def engine_name(self) -> str:
        return "Ollama"

    def is_available(self) -> bool:
        try:
            if self._client:
                self._client.list()
            else:
                self._ollama_module.list()
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            if self._client:
                result = self._client.list()
            else:
                result = self._ollama_module.list()
            # Support both ollama SDK response shapes
            models = result.get("models", result) if isinstance(result, dict) else result
            return [m.get("model", m.get("name", "")) for m in models]
        except Exception as e:
            logger.error(f"[Runtime] list_models failed: {e}")
            return []

    def chat(self, model: str, messages: list[dict]) -> str:
        try:
            if self._client:
                response = self._client.chat(model=model, messages=messages)
            else:
                response = self._ollama_module.chat(model=model, messages=messages)

            # Handle both dict and object response shapes
            if isinstance(response, dict):
                return response["message"]["content"]
            return response.message.content
        except Exception as e:
            logger.error(f"[Runtime] chat failed (model={model}): {e}")
            raise RuntimeError(f"Inference failed: {e}") from e


# ─────────────────────────────────────────────────────────────────────────────
# Future Engine Stubs (implement when needed — zero changes to ai.py required)
# ─────────────────────────────────────────────────────────────────────────────

class LlamaCppEngine(InferenceEngine):
    """
    Future: Direct llama.cpp integration via llama-cpp-python.
    Benefit: No external binary dependency. IGRIS owns the process.
    """

    @property
    def engine_name(self) -> str:
        return "llama.cpp"

    def is_available(self) -> bool:
        try:
            import llama_cpp  # noqa: F401
            return True
        except ImportError:
            return False

    def list_models(self) -> list[str]:
        raise NotImplementedError("LlamaCppEngine not yet implemented")

    def chat(self, model: str, messages: list[dict]) -> str:
        raise NotImplementedError("LlamaCppEngine not yet implemented")


class IGRISFoundationEngine(InferenceEngine):
    """
    Future: IGRIS M1 / IGRIS M2 / IGRIS Foundation Model.
    When IGRIS trains its own model, this engine will be the default.
    The rest of the codebase remains unchanged.
    """

    @property
    def engine_name(self) -> str:
        return "IGRIS Foundation"

    def is_available(self) -> bool:
        return False  # not yet built

    def list_models(self) -> list[str]:
        return ["igris-m1", "igris-m2"]

    def chat(self, model: str, messages: list[dict]) -> str:
        raise NotImplementedError("IGRIS Foundation Model not yet released")


# ─────────────────────────────────────────────────────────────────────────────
# Factory — get the best available engine
# ─────────────────────────────────────────────────────────────────────────────

_engine_instance: Optional[InferenceEngine] = None


def get_inference_engine(preferred: str = "ollama") -> InferenceEngine:
    """
    Returns a cached inference engine instance.

    Falls back gracefully:
      ollama → (future: llama.cpp) → raises RuntimeError

    Usage:
        from engine.models.local_models import get_inference_engine
        engine = get_inference_engine()
        reply = engine.chat("llama3.2:3b", messages)
    """
    global _engine_instance

    if _engine_instance is not None:
        return _engine_instance

    candidates = {
        "ollama": OllamaEngine,
        "llama_cpp": LlamaCppEngine,
        "igris_foundation": IGRISFoundationEngine,
    }

    engine_class = candidates.get(preferred, OllamaEngine)
    engine = engine_class()

    if engine.is_available():
        logger.info(f"[Runtime] Using engine: {engine.engine_name}")
        _engine_instance = engine
        return engine

    # Fallback chain
    for name, cls in candidates.items():
        if name == preferred:
            continue
        fallback = cls()
        if fallback.is_available():
            logger.warning(
                f"[Runtime] '{preferred}' unavailable. Falling back to: {fallback.engine_name}"
            )
            _engine_instance = fallback
            return fallback

    raise RuntimeError(
        "[IGRIS Runtime] No inference engine is available. "
        "Please ensure Ollama is installed and running: https://ollama.com"
    )


def reset_engine():
    """Force the engine to re-initialise on next call. Used in tests."""
    global _engine_instance
    _engine_instance = None
