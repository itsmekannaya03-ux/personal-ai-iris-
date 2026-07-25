"""
ModelManager — Model lifecycle management.

Handles:
  - Model registration and discovery
  - Version tracking
  - Hot-swapping between models
  - Model metadata and configuration
"""

import json
import os
import logging
import subprocess
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("iris.model_manager")


@dataclass
class ModelInfo:
    name: str
    provider: str  # ollama, openai, custom
    version: str = "1.0.0"
    capabilities: list[str] = field(default_factory=list)
    size: str = "unknown"
    description: str = ""
    loaded: bool = False
    active: bool = False
    config: dict = field(default_factory=dict)


class ModelManager:
    """
    Manages all AI models available to the system.
    Supports multiple providers and hot-swapping.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(
            os.path.expanduser("~"), ".igris", "models.json"
        )
        self._models: dict[str, ModelInfo] = {}
        self._active_model: Optional[str] = None
        self._load_config()
        logger.info(f"Model manager initialized ({len(self._models)} models registered)")

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                for name, info in data.get("models", {}).items():
                    self._models[name] = ModelInfo(**info)
                self._active_model = data.get("active_model")
                logger.info(f"Loaded {len(self._models)} models from config")
            except Exception as e:
                logger.error(f"Failed to load model config: {e}")

    def _save_config(self):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            data = {
                "models": {name: info.__dict__ for name, info in self._models.items()},
                "active_model": self._active_model,
                "updated_at": datetime.now().isoformat(),
            }
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save model config: {e}")

    def scan_ollama_models(self) -> list[str]:
        """Discover models available in Ollama."""
        discovered = []
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if parts:
                        name = parts[0]
                        self.register_model(
                            name=name,
                            provider="ollama",
                            description=f"Ollama model: {name}",
                        )
                        discovered.append(name)
                logger.info(f"Discovered {len(discovered)} Ollama models")
        except Exception as e:
            logger.error(f"Failed to scan Ollama models: {e}")
        return discovered

    def register_model(self, name: str, provider: str, **kwargs) -> ModelInfo:
        model = ModelInfo(name=name, provider=provider, **kwargs)
        self._models[name] = model
        self._save_config()
        logger.info(f"Registered model: {name} ({provider})")
        return model

    def unregister_model(self, name: str) -> bool:
        if name in self._models:
            del self._models[name]
            if self._active_model == name:
                self._active_model = None
            self._save_config()
            logger.info(f"Unregistered model: {name}")
            return True
        return False

    def activate_model(self, name: str) -> bool:
        if name not in self._models:
            logger.error(f"Model '{name}' not found")
            return False
        if self._active_model:
            self._models[self._active_model].active = False
        self._models[name].active = True
        self._models[name].loaded = True
        self._active_model = name
        self._save_config()
        logger.info(f"Activated model: {name}")
        return True

    def get_active_model(self) -> Optional[ModelInfo]:
        if self._active_model and self._active_model in self._models:
            return self._models[self._active_model]
        return None

    def get_model(self, name: str) -> Optional[ModelInfo]:
        return self._models.get(name)

    def list_models(self) -> list[dict]:
        return [
            {
                "name": m.name,
                "provider": m.provider,
                "version": m.version,
                "capabilities": m.capabilities,
                "size": m.size,
                "description": m.description,
                "active": m.active,
                "loaded": m.loaded,
            }
            for m in self._models.values()
        ]

    def update_model_config(self, name: str, config: dict) -> bool:
        if name not in self._models:
            return False
        self._models[name].config.update(config)
        self._save_config()
        return True

    def get_status(self) -> dict:
        return {
            "total_models": len(self._models),
            "active_model": self._active_model,
            "models": self.list_models(),
            "config_path": self.config_path,
        }
