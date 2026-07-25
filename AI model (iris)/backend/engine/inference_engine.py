"""
InferenceEngine — Model inference abstraction.

Supports multiple backends:
  1. Ollama (local, default)
  2. OpenAI-compatible API
  3. Custom model loaded directly
  4. Fallback rule-based mode when no model is available

The engine automatically selects the best available backend.
"""

import json
import logging
import subprocess
import time
import re
from typing import Optional, Generator
from enum import Enum

logger = logging.getLogger("iris.inference")


class BackendType(Enum):
    AUTO = "auto"
    OLLAMA = "ollama"
    OPENAI = "openai"
    GROQ = "groq"
    CUSTOM = "custom"
    RULE_BASED = "rule_based"


class InferenceEngine:
    """
    Handles all model inference. Abstracts away the backend so
    the brain never has to think about where responses come from.
    """

    BACKEND_PRIORITY = ["ollama", "groq", "openai", "rule_based"]

    def __init__(self, config: Optional[dict] = None, api_key_manager=None):
        self.config = config or {}
        self.backend = BackendType(self.config.get("backend", "auto"))
        self.model_name = self.config.get("model_name", "llama3.2")
        self.ollama_url = self.config.get("ollama_url", "http://localhost:11434")
        self.api_key = self.config.get("api_key", "")
        self.api_url = self.config.get("api_url", "")
        self.max_tokens = self.config.get("max_tokens", 2048)
        self.temperature = self.config.get("temperature", 0.7)
        self.timeout = self.config.get("timeout", 60)
        self._api_key_manager = api_key_manager
        self._providers: list[BackendType] = []
        self._active_provider: Optional[BackendType] = None

        self._resolve_keys()
        self._available = False
        self._detect_backend()

        if self.backend == BackendType.AUTO:
            logger.info(f"Inference engine initialized (mode=auto, providers={[p.value for p in self._providers]}, model={self.model_name})")
        else:
            logger.info(f"Inference engine initialized (backend={self.backend.value}, model={self.model_name})")

    def _resolve_keys(self):
        if not self._api_key_manager:
            return
        self._keys = {
            "groq": self._api_key_manager.get_key("groq"),
            "openai": self._api_key_manager.get_key("openai"),
            "anthropic": self._api_key_manager.get_key("anthropic"),
            "google": self._api_key_manager.get_key("google"),
            "deepseek": self._api_key_manager.get_key("deepseek"),
            "mistral": self._api_key_manager.get_key("mistral"),
            "together": self._api_key_manager.get_key("together"),
            "cohere": self._api_key_manager.get_key("cohere"),
        }
        self._urls = {
            "groq": "https://api.groq.com/openai/v1",
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "google": "https://generativelanguage.googleapis.com/v1beta",
            "deepseek": "https://api.deepseek.com/v1",
            "mistral": "https://api.mistral.ai/v1",
            "together": "https://api.together.xyz/v1",
            "cohere": "https://api.cohere.ai/v1",
        }

    def _detect_backend(self):
        if self.backend == BackendType.AUTO:
            self._providers = self._detect_available_providers()
            self._available = len(self._providers) > 0
            if self._providers:
                self._active_provider = self._providers[0]
            return

        if self.backend == BackendType.OLLAMA:
            self._available = self._check_ollama()
        elif self.backend == BackendType.OPENAI:
            self._available = bool(self.api_key)
        elif self.backend == BackendType.GROQ:
            self._available = bool(self.api_key)
        elif self.backend == BackendType.CUSTOM:
            self._available = True
        else:
            self._available = True

    def _detect_available_providers(self) -> list[BackendType]:
        available = []
        for name in self.BACKEND_PRIORITY:
            if name == "ollama":
                if self._check_ollama():
                    available.append(BackendType.OLLAMA)
            elif name == "groq":
                key = getattr(self, '_keys', {}).get("groq") or self.api_key
                if key:
                    available.append(BackendType.GROQ)
            elif name == "openai":
                key = getattr(self, '_keys', {}).get("openai") or self.api_key
                if key:
                    available.append(BackendType.OPENAI)
            elif name == "rule_based":
                available.append(BackendType.RULE_BASED)
        logger.info(f"Available providers: {[p.value for p in available]}")
        return available

    def _check_ollama(self) -> bool:
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                models = result.stdout.lower()
                if self.model_name.lower() in models:
                    logger.info(f"Ollama model '{self.model_name}' found")
                    return True
                logger.warning(f"Ollama model '{self.model_name}' not found. Available:\n{result.stdout}")
                return False
            return False
        except FileNotFoundError:
            logger.warning("Ollama not installed")
            return False
        except Exception as e:
            logger.warning(f"Ollama check failed: {e}")
            return False

    def _call_ollama(self, prompt: str, system_prompt: str = "") -> str:
        import urllib.request
        import urllib.error

        data = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "num_predict": self.max_tokens,
                "temperature": self.temperature,
            }
        }
        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode())
                return result.get("response", "")
        except urllib.error.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e.code} {e.reason}")
            raise
        except urllib.error.URLError as e:
            logger.error(f"Ollama connection error: {e.reason}")
            raise

    def _rule_based_response(self, prompt: str) -> str:
        """Fallback when no model is available."""
        prompt_lower = prompt.lower().strip()

        greetings = ["hello", "hi", "hey", "good morning", "good evening"]
        if any(g in prompt_lower for g in greetings):
            return "Hello! I'm Jarvis, your personal AI assistant. How can I help you today?"

        questions = ["who", "what", "when", "where", "why", "how", "tell me"]
        if any(q in prompt_lower for q in questions):
            return f"That's an interesting question. Based on my knowledge, I can tell you about \"{prompt}\". However, for the most accurate response, I recommend connecting me to a proper AI model."

        if "help" in prompt_lower or "can you" in prompt_lower:
            return "I can help you with a variety of tasks: answering questions, searching the web, controlling your computer, remembering information, and more. What would you like me to do?"

        return f"I understand you said: \"{prompt}\". I'm currently running in fallback mode. For full capability, please install Ollama with {self.model_name}."

    # ─── Public API ───────────────────────────────────────────

    def _call_openai_chat(self, prompt: str, system_prompt: str = "", stream: bool = False):
        """Shared OpenAI-compatible call (OpenAI, Groq, etc.)."""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.api_url or None)
        return client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=stream,
        )

    def _call_groq_stream(self, prompt: str, system_prompt: str = "") -> Generator[str, None, None]:
        """SSE streaming via Groq's OpenAI-compatible endpoint."""
        try:
            response = self._call_openai_chat(prompt, system_prompt, stream=True)
            for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except Exception as e:
            logger.error(f"Groq stream error: {e}")
            yield self._rule_based_response(prompt)

    def _call_openai_stream(self, prompt: str, system_prompt: str = "") -> Generator[str, None, None]:
        """SSE streaming via any OpenAI-compatible API."""
        try:
            response = self._call_openai_chat(prompt, system_prompt, stream=True)
            for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except Exception as e:
            logger.error(f"OpenAI stream error: {e}")
            yield self._rule_based_response(prompt)

    def generate(self, prompt: str, system_prompt: str = "", stream: bool = False) -> str:
        """Generate a response. In AUTO mode, tries each provider until one works."""
        if self.backend == BackendType.AUTO:
            return self._generate_auto(prompt, system_prompt)

        if self.backend in (BackendType.OPENAI, BackendType.GROQ) and self._available:
            try:
                response = self._call_openai_chat(prompt, system_prompt, stream=False)
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"API inference failed, falling back: {e}")
                return self._rule_based_response(prompt)
        elif self.backend == BackendType.OLLAMA and self._available:
            try:
                return self._call_ollama(prompt, system_prompt)
            except Exception as e:
                logger.error(f"Ollama inference failed, falling back: {e}")
                return self._rule_based_response(prompt)
        else:
            return self._rule_based_response(prompt)

    def _generate_auto(self, prompt: str, system_prompt: str = "") -> str:
        for provider in self._providers:
            if provider == BackendType.OLLAMA:
                try:
                    return self._call_ollama(prompt, system_prompt)
                except Exception as e:
                    logger.warning(f"Ollama failed ({e}), trying next provider...")
            elif provider == BackendType.GROQ:
                try:
                    key = getattr(self, '_keys', {}).get("groq")
                    if not key:
                        continue
                    from openai import OpenAI
                    client = OpenAI(api_key=key, base_url=self._urls["groq"])
                    model = self.model_name if self.model_name != "llama3.2" else "llama3-8b-8192"
                    response = client.chat.completions.create(
                        model=model, messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ], max_tokens=self.max_tokens, temperature=self.temperature,
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    logger.warning(f"Groq failed ({e}), trying next provider...")
            elif provider == BackendType.OPENAI:
                try:
                    key = getattr(self, '_keys', {}).get("openai")
                    if not key:
                        continue
                    from openai import OpenAI
                    client = OpenAI(api_key=key)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini", messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ], max_tokens=self.max_tokens, temperature=self.temperature,
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    logger.warning(f"OpenAI failed ({e}), trying next provider...")
            elif provider == BackendType.RULE_BASED:
                return self._rule_based_response(prompt)
        return self._rule_based_response(prompt)

    def generate_stream(self, prompt: str, system_prompt: str = "") -> Generator[str, None, None]:
        """Stream tokens. In AUTO mode, tries each provider until one works."""
        if self.backend == BackendType.AUTO:
            yield from self._generate_stream_auto(prompt, system_prompt)
        elif self.backend == BackendType.GROQ and self._available:
            yield from self._call_groq_stream(prompt, system_prompt)
        elif self.backend == BackendType.OPENAI and self._available:
            yield from self._call_openai_stream(prompt, system_prompt)
        elif self.backend == BackendType.OLLAMA and self._available:
            import urllib.request
            import urllib.error

            data = {
                "model": self.model_name,
                "prompt": prompt,
                "system": system_prompt,
                "stream": True,
                "options": {
                    "num_predict": self.max_tokens,
                    "temperature": self.temperature,
                }
            }
            req = urllib.request.Request(
                f"{self.ollama_url}/api/generate",
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    buffer = ""
                    for chunk in resp:
                        buffer += chunk.decode()
                        try:
                            obj = json.loads(buffer)
                            token = obj.get("response", "")
                            if token:
                                yield token
                            if obj.get("done"):
                                break
                            buffer = ""
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.error(f"Ollama stream error: {e}")
                yield self._rule_based_response(prompt)
        else:
            yield self._rule_based_response(prompt)

    def _generate_stream_auto(self, prompt: str, system_prompt: str = "") -> Generator[str, None, None]:
        for provider in self._providers:
            if provider == BackendType.OLLAMA:
                try:
                    yield from self._stream_ollama(prompt, system_prompt)
                    return
                except Exception as e:
                    logger.warning(f"Ollama stream failed ({e}), trying next...")
            elif provider == BackendType.GROQ:
                try:
                    key = getattr(self, '_keys', {}).get("groq")
                    if not key:
                        continue
                    from openai import OpenAI
                    client = OpenAI(api_key=key, base_url=self._urls["groq"])
                    model = self.model_name if self.model_name != "llama3.2" else "llama3-8b-8192"
                    response = client.chat.completions.create(
                        model=model, messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ], max_tokens=self.max_tokens, temperature=self.temperature, stream=True,
                    )
                    for chunk in response:
                        delta = chunk.choices[0].delta if chunk.choices else None
                        if delta and delta.content:
                            yield delta.content
                    return
                except Exception as e:
                    logger.warning(f"Groq stream failed ({e}), trying next...")
            elif provider == BackendType.OPENAI:
                try:
                    key = getattr(self, '_keys', {}).get("openai")
                    if not key:
                        continue
                    from openai import OpenAI
                    client = OpenAI(api_key=key)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini", messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ], max_tokens=self.max_tokens, temperature=self.temperature, stream=True,
                    )
                    for chunk in response:
                        delta = chunk.choices[0].delta if chunk.choices else None
                        if delta and delta.content:
                            yield delta.content
                    return
                except Exception as e:
                    logger.warning(f"OpenAI stream failed ({e}), trying next...")
            elif provider == BackendType.RULE_BASED:
                yield self._rule_based_response(prompt)
                return

    def _stream_ollama(self, prompt: str, system_prompt: str = ""):
        import urllib.request
        import urllib.error
        data = {
            "model": self.model_name, "prompt": prompt, "system": system_prompt, "stream": True,
            "options": {"num_predict": self.max_tokens, "temperature": self.temperature},
        }
        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=json.dumps(data).encode(), headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            buffer = ""
            for chunk in resp:
                buffer += chunk.decode()
                try:
                    obj = json.loads(buffer)
                    token = obj.get("response", "")
                    if token:
                        yield token
                    if obj.get("done"):
                        break
                    buffer = ""
                except json.JSONDecodeError:
                    continue

    def get_status(self) -> dict:
        status = {
            "backend": self.backend.value,
            "model": self.model_name,
            "available": self._available,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if self.backend == BackendType.AUTO:
            status["providers"] = [p.value for p in self._providers]
            status["active_provider"] = self._active_provider.value if self._active_provider else None
        return status

    def embed(self, text: str) -> list[float]:
        """Generate embeddings for text (for memory search)."""
        if self.backend == BackendType.OLLAMA:
            import urllib.request
            import json
            data = {
                "model": self.model_name,
                "prompt": text,
            }
            req = urllib.request.Request(
                f"{self.ollama_url}/api/embeddings",
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read().decode())
                    return result.get("embedding", [])
            except Exception as e:
                logger.error(f"Embedding failed: {e}")
                return []
        return []
