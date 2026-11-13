"""
IRIS Runtime — Model Manager

Responsibility: Given a task type (coding, reasoning, general chat, etc.),
return the best available model for that task.

Design principles:
  1. The user NEVER manually selects a model.
  2. IRIS selects the best available model automatically.
  3. If the preferred model is not installed, fall back gracefully.
  4. The task→model mapping is configurable (will move to a database record).

Current model catalogue (Phase 1):
  Task          | Preferred Model         | Why
  -------------|-------------------------|-----
  general      | llama3.2:3b             | Fast, good for everyday chat
  coding       | qwen2.5-coder:7b        | State-of-the-art code generation
  reasoning    | deepseek-r1:7b          | Chain-of-thought reasoning
  fast_reply   | gemma2:2b               | Minimal latency, short responses
  creative     | llama3.2:3b             | Creative writing, storytelling
  analysis     | deepseek-r1:7b          | Data analysis, logical breakdown
  image_prompt | llama3.2:3b             | Prompt engineering for image gen

Phase 2 / 3 will add:
  - iris-m1   Once the IRIS foundation model begins fine-tuning
  - iris-m2   Reduced dependency on external models
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("iris.runtime.model_manager")


# ─────────────────────────────────────────────────────────────────────────────
# Task types — the only vocabulary the rest of IRIS uses
# ─────────────────────────────────────────────────────────────────────────────

TASK_GENERAL      = "general"
TASK_CODING       = "coding"
TASK_REASONING    = "reasoning"
TASK_FAST_REPLY   = "fast_reply"
TASK_CREATIVE     = "creative"
TASK_ANALYSIS     = "analysis"
TASK_IMAGE_PROMPT = "image_prompt"

ALL_TASK_TYPES = [
    TASK_GENERAL, TASK_CODING, TASK_REASONING,
    TASK_FAST_REPLY, TASK_CREATIVE, TASK_ANALYSIS, TASK_IMAGE_PROMPT,
]


@dataclass
class ModelConfig:
    """Describes a model's capabilities used for selection and fallback."""
    model_id: str               # e.g. "qwen2.5-coder:7b"
    display_name: str           # e.g. "Qwen 2.5 Coder 7B"
    task_types: list[str]       # tasks this model is good at
    min_vram_gb: float = 4.0    # rough VRAM requirement
    is_fast: bool = False       # True if it's a lightweight fast model
    description: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Default model catalogue
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_CATALOGUE: list[ModelConfig] = [
    ModelConfig(
        model_id="llama3.2:3b",
        display_name="LLaMA 3.2 3B",
        task_types=[TASK_GENERAL, TASK_CREATIVE, TASK_IMAGE_PROMPT],
        min_vram_gb=3.0,
        description="Default model — fast, well-rounded, everyday assistant",
    ),
    ModelConfig(
        model_id="qwen2.5-coder:7b",
        display_name="Qwen 2.5 Coder 7B",
        task_types=[TASK_CODING],
        min_vram_gb=6.0,
        description="Best-in-class open-source code generation model",
    ),
    ModelConfig(
        model_id="deepseek-r1:7b",
        display_name="DeepSeek R1 7B",
        task_types=[TASK_REASONING, TASK_ANALYSIS],
        min_vram_gb=6.0,
        description="Chain-of-thought reasoning and analytical tasks",
    ),
    ModelConfig(
        model_id="gemma2:2b",
        display_name="Gemma 2 2B",
        task_types=[TASK_FAST_REPLY],
        min_vram_gb=2.0,
        is_fast=True,
        description="Ultra-fast replies for quick queries, status checks",
    ),
    # Future phase — uncomment when fine-tuning begins
    # ModelConfig(
    #     model_id="iris-m1",
    #     display_name="IRIS M1",
    #     task_types=ALL_TASK_TYPES,
    #     min_vram_gb=4.0,
    #     description="IRIS Foundation Model — Phase 3 roadmap",
    # ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Intent → Task type mapping
# Maps IntentDetector intents to ModelManager task types
# ─────────────────────────────────────────────────────────────────────────────

INTENT_TO_TASK: dict[str, str] = {
    "general":         TASK_GENERAL,
    "realtime":        TASK_FAST_REPLY,
    "open":            TASK_FAST_REPLY,
    "close":           TASK_FAST_REPLY,
    "search":          TASK_GENERAL,
    "reminder":        TASK_FAST_REPLY,
    "system":          TASK_FAST_REPLY,
    "content":         TASK_CREATIVE,
    "media":           TASK_FAST_REPLY,
    "image_generation":TASK_IMAGE_PROMPT,
    "command":         TASK_GENERAL,
    # Coding intent — detected by keyword analysis in ai.py
    "code":            TASK_CODING,
    "coding":          TASK_CODING,
    "analysis":        TASK_ANALYSIS,
    "reasoning":       TASK_REASONING,
}

# Keywords that override the intent detector for model selection
CODING_KEYWORDS = [
    "code", "function", "debug", "error", "python", "javascript",
    "typescript", "java", "c++", "rust", "sql", "algorithm",
    "implement", "refactor", "class", "module", "script", "api",
]

REASONING_KEYWORDS = [
    "explain why", "analyze", "compare", "pros and cons", "difference between",
    "evaluate", "assess", "logical", "reasoning", "step by step", "think through",
]


# ─────────────────────────────────────────────────────────────────────────────
# Model Manager
# ─────────────────────────────────────────────────────────────────────────────

class ModelManager:
    """
    Selects the best available model for a given task.

    Usage:
        from engine.models.model_manager import ModelManager
        mm = ModelManager()
        model = mm.select_model("coding", available_models=["llama3.2:3b"])
        # Returns "llama3.2:3b" because qwen isn't available
    """

    def __init__(
        self,
        catalogue: Optional[list[ModelConfig]] = None,
        fallback_model: str = "llama3.2:3b",
    ):
        self._catalogue = catalogue or DEFAULT_CATALOGUE
        self._fallback = fallback_model
        self._available_cache: Optional[list[str]] = None

        # task_type → ordered list of model_ids (best first)
        self._task_map: dict[str, list[str]] = self._build_task_map()

    def _build_task_map(self) -> dict[str, list[str]]:
        task_map: dict[str, list[str]] = {t: [] for t in ALL_TASK_TYPES}
        for cfg in self._catalogue:
            for task in cfg.task_types:
                if task in task_map:
                    task_map[task].append(cfg.model_id)
        return task_map

    def set_available_models(self, models: list[str]):
        """Cache the list of currently installed models (from engine.list_models())."""
        self._available_cache = models
        logger.debug(f"[ModelManager] Available models updated: {models}")

    def detect_task_type(self, message: str, intent: str) -> str:
        """
        Determine the best task type from the message and detected intent.
        Keyword analysis overrides the intent detector for precision.
        """
        msg_lower = message.lower()

        # Explicit override by keyword
        if any(kw in msg_lower for kw in CODING_KEYWORDS):
            return TASK_CODING
        if any(kw in msg_lower for kw in REASONING_KEYWORDS):
            return TASK_REASONING

        # Map from intent detector result
        return INTENT_TO_TASK.get(intent, TASK_GENERAL)

    def select_model(
        self,
        task_type: str,
        available_models: Optional[list[str]] = None,
    ) -> str:
        """
        Returns the best available model for the given task type.

        Falls back to the next suitable model, then to the global fallback.
        Never raises — always returns a usable model string.

        Args:
            task_type: One of the TASK_* constants
            available_models: Override the cached list (useful for tests)

        Returns:
            Model identifier string (e.g., 'llama3.2:3b')
        """
        available = available_models or self._available_cache or []

        preferred_models = self._task_map.get(task_type, [])

        for model_id in preferred_models:
            if not available or model_id in available:
                logger.debug(
                    f"[ModelManager] Selected '{model_id}' for task '{task_type}'"
                )
                return model_id

        # If no preferred model available, try general models
        if task_type != TASK_GENERAL:
            for model_id in self._task_map.get(TASK_GENERAL, []):
                if not available or model_id in available:
                    logger.warning(
                        f"[ModelManager] No '{task_type}' model available. "
                        f"Using general model: '{model_id}'"
                    )
                    return model_id

        # Final fallback
        logger.warning(
            f"[ModelManager] No suitable model found for '{task_type}'. "
            f"Falling back to: '{self._fallback}'"
        )
        return self._fallback

    def get_model_info(self, model_id: str) -> Optional[ModelConfig]:
        """Returns ModelConfig for a given model_id, or None."""
        for cfg in self._catalogue:
            if cfg.model_id == model_id:
                return cfg
        return None

    def list_task_assignments(self) -> dict[str, str]:
        """Returns a dict of {task_type: best_model_id} for all tasks."""
        available = self._available_cache or []
        return {
            task: self.select_model(task, available)
            for task in ALL_TASK_TYPES
        }

    def get_missing_models(self) -> list[ModelConfig]:
        """Returns models in the catalogue that are not yet installed."""
        available = self._available_cache or []
        return [cfg for cfg in self._catalogue if cfg.model_id not in available]

    def get_missing_for_task(self, task_type: str) -> Optional[ModelConfig]:
        """Returns the best model for this task if it's not installed."""
        available = self._available_cache or []
        for model_id in self._task_map.get(task_type, []):
            if model_id not in available:
                return self.get_model_info(model_id)
        return None

    def get_download_suggestion(self, task_type: str) -> Optional[str]:
        """Returns a download command for the best missing model for this task."""
        missing = self.get_missing_for_task(task_type)
        if missing:
            return f"ollama pull {missing.model_id}"
        return None

    def get_upgrade_path(self) -> list[dict]:
        """Returns a prioritized list of model upgrades to suggest to the user."""
        available = self._available_cache or []
        suggestions = []
        for task in TASK_REASONING, TASK_CODING:
            for model_id in self._task_map.get(task, []):
                if model_id not in available:
                    cfg = self.get_model_info(model_id)
                    if cfg:
                        suggestions.append({
                            "model_id": model_id,
                            "display_name": cfg.display_name,
                            "task": task,
                            "description": cfg.description,
                            "download_command": f"ollama pull {model_id}",
                        })
                    break
        return suggestions


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_manager_instance: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Returns a shared ModelManager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ModelManager()
    return _manager_instance
