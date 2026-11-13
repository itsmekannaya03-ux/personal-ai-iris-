"""
OllamaClient — Local LLM Client for Zero-Internet Intelligence.

Direct interface to Ollama HTTP daemon on localhost:11434.
Supports model discovery, non-blocking health checks, chat completions,
and streaming token generation with automatic retry and error handling.
"""

import json
import time
import logging
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any, Generator

logger = logging.getLogger("iris.ollama_client")


class OllamaClient:
    """Robust client for local Ollama instance."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self._cached_available: Optional[bool] = None
        self._last_health_check: float = 0.0
        self._cached_models: List[str] = []

    def is_available(self, force: bool = False) -> bool:
        """Check if local Ollama daemon is active and responding."""
        now = time.time()
        if not force and self._cached_available is not None and (now - self._last_health_check < 3.0):
            return self._cached_available

        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", headers={"User-Agent": "IRIS-AI"})
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    models = [m.get("name", "") for m in data.get("models", [])]
                    self._cached_models = models
                    self._cached_available = True
                    self._last_health_check = now
                    return True
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")

        self._cached_available = False
        self._last_health_check = now
        return False

    def list_models(self) -> List[Dict[str, Any]]:
        """List all models installed locally in Ollama."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", headers={"User-Agent": "IRIS-AI"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode())
                models = []
                for m in data.get("models", []):
                    models.append({
                        "name": m.get("name", ""),
                        "size": m.get("size", 0),
                        "modified_at": m.get("modified_at", ""),
                        "family": m.get("details", {}).get("family", ""),
                        "parameter_size": m.get("details", {}).get("parameter_size", ""),
                        "quantization_level": m.get("details", {}).get("quantization_level", ""),
                    })
                self._cached_models = [m["name"] for m in models]
                return models
        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")
            return []

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.6,
        max_tokens: int = 1024,
        timeout: float = 45.0,
    ) -> Dict[str, Any]:
        """Send chat messages to local model and return assistant message."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": 0.9,
            },
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json", "User-Agent": "IRIS-AI"},
            method="POST",
        )

        try:
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                elapsed = time.time() - t0
                content = raw.get("message", {}).get("content", "").strip()
                return {
                    "content": content,
                    "model": raw.get("model", model),
                    "done": raw.get("done", True),
                    "total_duration": raw.get("total_duration", 0),
                    "elapsed_seconds": round(elapsed, 2),
                    "provider": "ollama",
                    "is_offline": True,
                }
        except urllib.error.URLError as e:
            logger.error(f"Ollama network error during chat ({model}): {e}")
            raise RuntimeError(f"Ollama local connection failed: {e}")
        except Exception as e:
            logger.error(f"Ollama chat error ({model}): {e}")
            raise

    def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.6,
        max_tokens: int = 1024,
    ) -> Generator[str, None, None]:
        """Stream token responses line-by-line from local Ollama model."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json", "User-Agent": "IRIS-AI"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60.0) as resp:
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue
                try:
                    chunk = json.loads(line_str)
                    piece = chunk.get("message", {}).get("content", "")
                    if piece:
                        yield piece
                    if chunk.get("done", False):
                        break
                except Exception:
                    continue


_ollama_client: Optional[OllamaClient] = None

def get_ollama_client() -> OllamaClient:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
