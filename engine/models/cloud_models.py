"""
IGRIS Runtime — Cloud Provider Abstraction

When a query can't be handled locally (or PIE determines cloud routing is safe),
this module handles the cloud inference call.

Design:
  - Abstract CloudProvider base (replaceable: OpenAI, Anthropic, custom, etc.)
  - StubCloudProvider that returns helpful messages about configuration
  - Factory function with config-driven selection

Phase 2 will add:
  - OpenAI-compatible provider (works with any OpenAI API endpoint)
  - Configurable per-provider API keys stored in encrypted config
  - Cost tracking per query
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger("igris.runtime.cloud")


class CloudProvider(ABC):
    @abstractmethod
    def query(self, messages: list[dict], model: Optional[str] = None) -> str:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        pass


class StubCloudProvider(CloudProvider):
    @property
    def provider_name(self) -> str:
        return "Stub (not configured)"

    def is_configured(self) -> bool:
        return False

    def query(self, messages: list[dict], model: Optional[str] = None) -> str:
        return (
            "Cloud AI services are not configured. "
            "To enable hybrid intelligence, set up a cloud provider "
            "in your privacy profile. "
            "IGRIS will automatically anonymize sensitive data before sending it."
        )


class OpenAICompatibleProvider(CloudProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", default_model: str = "gpt-4o-mini"):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._configured = bool(api_key and api_key != "your-api-key-here")

    @property
    def provider_name(self) -> str:
        return "OpenAI-Compatible"

    def is_configured(self) -> bool:
        return self._configured

    def query(self, messages: list[dict], model: Optional[str] = None) -> str:
        if not self._configured:
            return "Cloud provider not configured. Set your API key in privacy settings."
        try:
            import httpx
            resp = httpx.post(
                f"{self._base_url}/chat/completions",
                json={
                    "model": model or self._default_model,
                    "messages": messages,
                    "max_tokens": 2048,
                },
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"[Cloud] Query failed: {e}")
            return f"Cloud query failed: {e}"


_cloud_instance: Optional[CloudProvider] = None


def get_cloud_provider(provider_type: str = "stub", **kwargs) -> CloudProvider:
    global _cloud_instance
    if _cloud_instance is not None:
        return _cloud_instance

    providers = {
        "stub": StubCloudProvider,
        "openai": OpenAICompatibleProvider,
    }

    cls = providers.get(provider_type, StubCloudProvider)
    instance = cls(**kwargs) if kwargs else cls()
    _cloud_instance = instance
    logger.info(f"[Runtime] Cloud provider: {instance.provider_name}")
    return instance


def reset_cloud_provider():
    global _cloud_instance
    _cloud_instance = None
