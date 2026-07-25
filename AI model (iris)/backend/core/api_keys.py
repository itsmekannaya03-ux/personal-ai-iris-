"""
API Keys — Multi-key management for model providers.

Loads API keys from .env file, supports up to 20 keys
in numbered slots (MODEL_API_KEY_0-19) plus named keys
for specific providers.

Features:
  - Load from .env or environment variables
  - Key rotation (round-robin across available keys)
  - Provider-based key lookup
  - Key validation (format checks)
  - Max 20 keys enforced
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional, Iterator
from dataclasses import dataclass, field

logger = logging.getLogger("iris.api_keys")

MAX_KEYS = 20

PROVIDER_PREFIXES = {
    "openai": ("sk-", "sk-proj-", "sk-svc-", "sk-ant-"),
    "anthropic": ("sk-ant-",),
    "google": ("AIza",),
    "groq": ("gsk_",),
    "deepseek": ("sk-",),
    "mistral": ("",),
    "together": ("",),
    "cohere": ("",),
}

NAMED_KEY_MAP = {
    "OPENAI_API_KEY": "openai",
    "ANTHROPIC_API_KEY": "anthropic",
    "GOOGLE_API_KEY": "google",
    "GROQ_API_KEY": "groq",
    "DEEPSEEK_API_KEY": "deepseek",
    "MISTRAL_API_KEY": "mistral",
    "TOGETHER_API_KEY": "together",
    "COHERE_API_KEY": "cohere",
}


@dataclass
class APIKey:
    key: str
    provider: str = "unknown"
    slot: int = -1
    valid: bool = False
    name: str = ""


class APIKeyManager:
    """
    Manages up to 20 model API keys.
    Loads from .env file, validates, and provides key rotation.
    """

    def __init__(self, env_path: Optional[str] = None):
        self._keys: list[APIKey] = []
        self._named_keys: dict[str, APIKey] = {}
        self._rotation_index = 0
        self._env_path = env_path or self._find_env()
        self._loaded = False
        self.load()

    def _find_env(self) -> str:
        """Locate the .env file relative to this module."""
        start = Path(__file__).resolve().parent.parent  # backend/
        candidates = [
            start / ".env",
            start / ".env.local",
            start.parent / ".env",  # AI model (iris)/
        ]
        for c in candidates:
            if c.exists():
                return str(c)
        return str(start / ".env")

    def load(self):
        """Load API keys from .env file and environment variables."""
        self._keys.clear()
        self._named_keys.clear()
        loaded_count = 0

        # Load from .env file
        env_file = Path(self._env_path)
        env_vars: dict[str, str] = {}
        if env_file.exists():
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, _, value = line.partition("=")
                        key = key.strip()
                        value = value.strip().strip("\"'")
                        env_vars[key] = value
                logger.info(f"Loaded {len(env_vars)} variables from {env_file.name}")
            except Exception as e:
                logger.error(f"Failed to load .env: {e}")

        # Also check OS environment (overrides .env)
        for var_name in list(env_vars.keys()) + [f"MODEL_API_KEY_{i}" for i in range(MAX_KEYS)] + list(NAMED_KEY_MAP.keys()):
            os_val = os.environ.get(var_name)
            if os_val:
                env_vars[var_name] = os_val

        # Load numbered slots (MODEL_API_KEY_0 through 19)
        for i in range(MAX_KEYS):
            var_name = f"MODEL_API_KEY_{i}"
            value = env_vars.get(var_name, "")
            value = value.strip()
            if value and len(value) > 4:
                provider = self._detect_provider(value)
                key_entry = APIKey(
                    key=value,
                    provider=provider,
                    slot=i,
                    valid=True,
                    name=f"Slot {i}",
                )
                self._keys.append(key_entry)
                loaded_count += 1

        # Load named keys
        for var_name, provider in NAMED_KEY_MAP.items():
            value = env_vars.get(var_name, "").strip()
            if value and len(value) > 4:
                key_entry = APIKey(
                    key=value,
                    provider=provider,
                    slot=-1,
                    valid=True,
                    name=var_name,
                )
                self._named_keys[provider] = key_entry
                if not any(k.key == value for k in self._keys):
                    self._keys.append(key_entry)
                    loaded_count += 1

        self._loaded = True
        logger.info(f"API key manager loaded {loaded_count} keys (max {MAX_KEYS})")

    def _detect_provider(self, key: str) -> str:
        """Detect provider from key prefix."""
        for provider, prefixes in PROVIDER_PREFIXES.items():
            for prefix in prefixes:
                if prefix and key.startswith(prefix):
                    return provider
        return "generic"

    def get_key(self, provider: Optional[str] = None) -> Optional[str]:
        """
        Get an API key, optionally filtered by provider.
        Uses round-robin rotation across available keys.
        """
        if not self._keys:
            return None

        if provider:
            provider_keys = [k for k in self._keys if k.provider == provider]
            if not provider_keys:
                # Fall back to any key
                provider_keys = self._keys
            idx = self._rotation_index % len(provider_keys)
            self._rotation_index += 1
            return provider_keys[idx].key

        idx = self._rotation_index % len(self._keys)
        self._rotation_index += 1
        return self._keys[idx].key

    def get_all_keys(self) -> list[str]:
        """Get all loaded API keys."""
        return [k.key for k in self._keys]

    def get_key_by_provider(self, provider: str) -> Optional[str]:
        """Get the first key matching the given provider."""
        for k in self._keys:
            if k.provider == provider:
                return k.key
        named = self._named_keys.get(provider)
        return named.key if named else None

    def add_key(self, key: str, provider: Optional[str] = None) -> bool:
        """Add a new API key. Returns False if max keys reached."""
        if len(self._keys) >= MAX_KEYS:
            logger.warning(f"Cannot add key: max {MAX_KEYS} keys reached")
            return False
        if not key or len(key) < 5:
            return False
        if any(k.key == key for k in self._keys):
            return False
        provider = provider or self._detect_provider(key)
        self._keys.append(APIKey(key=key, provider=provider, valid=True))
        logger.info(f"Added API key for provider '{provider}' ({len(self._keys)}/{MAX_KEYS})")
        return True

    def remove_key(self, key: str) -> bool:
        """Remove an API key by value."""
        for i, k in enumerate(self._keys):
            if k.key == key:
                self._keys.pop(i)
                logger.info(f"Removed API key ({len(self._keys)}/{MAX_KEYS})")
                return True
        return False

    def key_count(self) -> int:
        return len(self._keys)

    def providers_available(self) -> list[str]:
        """List unique providers with loaded keys."""
        return list(set(k.provider for k in self._keys))

    def has_key_for(self, provider: str) -> bool:
        """Check if any key is available for the given provider."""
        return any(k.provider == provider for k in self._keys)

    def rotate(self) -> Optional[str]:
        """Explicitly rotate to the next key and return it."""
        if not self._keys:
            return None
        self._rotation_index = (self._rotation_index + 1) % len(self._keys)
        return self._keys[self._rotation_index].key

    def get_status(self) -> dict:
        return {
            "loaded": self._loaded,
            "total_keys": len(self._keys),
            "max_keys": MAX_KEYS,
            "providers": self.providers_available(),
            "keys": [
                {
                    "slot": k.slot,
                    "provider": k.provider,
                    "name": k.name,
                    "masked": k.key[:8] + "..." + k.key[-4:] if len(k.key) > 12 else "***",
                    "valid": k.valid,
                }
                for k in self._keys
            ],
            "env_file": self._env_path,
        }
