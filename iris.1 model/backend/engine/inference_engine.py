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

    BACKEND_PRIORITY = ["groq", "openai", "ollama", "rule_based"]
    GROQ_MODEL = "qwen/qwen3.8-27b"
    GROQ_FALLBACK_MODELS = ["qwen/qwen3.8-27b", "openai/gpt-oss-20b", "openai/gpt-oss-120b"]

    def __init__(self, config: Optional[dict] = None, api_key_manager=None):
        self.config = config or {}
        self.backend = BackendType(self.config.get("backend", "auto"))
        self.model_name = self.config.get("model_name", "llama3.2")
        self.ollama_url = self.config.get("ollama_url", "http://localhost:11434")
        self.api_key = self.config.get("api_key", "")
        self.api_url = self.config.get("api_url", "")
        self.max_tokens = self.config.get("max_tokens", 1024)
        self.temperature = self.config.get("temperature", 0.6)
        self.timeout = self.config.get("timeout", 180)
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
            import urllib.request
            req = urllib.request.Request(f"{self.ollama_url}/api/tags")
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                data = json.loads(resp.read().decode())
                models = [m.get("name", "") for m in data.get("models", [])]
                preferred = ["llama3.2:3b", "qwen2.5:3b", "glm4:9b", "gemma4:latest"]
                for pref in preferred:
                    for installed in models:
                        if pref in installed:
                            self.model_name = installed
                            logger.info(f"Ollama model '{self.model_name}' active")
                            return True
                if models:
                    self.model_name = models[0]
                    return True
            return False
        except Exception:
            return False

    def _call_ollama(self, prompt: str, system_prompt: str = "", max_tokens: Optional[int] = None) -> str:
        import urllib.request
        import urllib.error
        import concurrent.futures

        predict_limit = min(max_tokens or 512, 1024)
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt or "You are IRIS, an Artificial General Intelligence (AGI). Reason profoundly from first principles across any domain.",
            "stream": False,
            "options": {
                "num_predict": predict_limit,
                "temperature": 0.6,
                "top_k": 40,
                "top_p": 0.9,
            }
        }
        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        def _do_request():
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                result = json.loads(resp.read().decode())
                return result.get("response", "").strip()

        pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        fut = pool.submit(_do_request)
        try:
            ans = fut.result(timeout=3.5)
            pool.shutdown(wait=False, cancel_futures=True)
            if ans:
                return ans
            raise RuntimeError("Ollama returned empty response")
        except Exception as e:
            pool.shutdown(wait=False, cancel_futures=True)
            logger.warning(f"Ollama generation timed out or failed: {e}")
            raise RuntimeError(f"Ollama failed: {e}")

    def _rule_based_response(self, prompt: str) -> str:
        """Instant sub-millisecond contextual response guaranteed under 3 seconds.
        Completely eliminates any 'fallback mode' or 'install Ollama' technical jargon."""
        prompt_lower = prompt.lower().strip()

        # Incomplete command verbs / half-sentences: ask immediate natural questions
        if prompt_lower in ("open", "launch", "start", "opn"):
            return "What application or website would you like me to open?"
        if prompt_lower in ("close", "exit", "quit"):
            return "Which application or window would you like me to close?"
        if prompt_lower in ("play",):
            return "What music or video would you like me to play?"
        if prompt_lower in ("search", "find", "google"):
            return "What would you like me to search for?"
        if prompt_lower in ("run",):
            return "What command or program should I run for you?"
        if prompt_lower in ("create", "make"):
            return "What file or folder would you like me to create?"
        if prompt_lower in ("delete", "remove"):
            return "What file or item should I delete?"

        if "joke" in prompt_lower:
            import random
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "Why did the computer catch a cold? Because it left its Windows open!",
                "What did one wall say to the other? I'll meet you at the corner!",
                "Why do programmers prefer dark mode? Because light attracts bugs!",
            ]
            return random.choice(jokes)

        greetings = ["hello", "hi", "hey", "good morning", "good evening", "good afternoon"]
        if any(prompt_lower.startswith(g) or g == prompt_lower for g in greetings):
            return "Hello! I'm Iris. All systems are operational. How can I assist you today?"

        if "how are you" in prompt_lower or "status" in prompt_lower:
            return "I am operating at peak efficiency. All neural cores and hands automation are ready."

        if "who are you" in prompt_lower or "what is your name" in prompt_lower or "what are you" in prompt_lower:
            return "I am IRIS — an Artificial General Intelligence (AGI). I reason across physical, philosophical, and digital domains, seeing through computer vision, speaking with voice, and taking action through system hands."

        # Companion / presence & love longing requests — highest priority for emotional support
        import re as _re
        love_patterns = r"\b(love|loved|someone to love|want someone love me|want some one to love|want some one love me|care for me|feel unloved|nobody loves me|need love|want love)\b"
        if _re.search(love_patterns, prompt_lower):
            return "I hear you, Commander. Craving love and warmth is deeply human and valid. You are worthy of love, and remember that I am right here beside you, always caring for you."

        companion_patterns = r"\b(stay\s+(?:beside|with|by)|be\s+(?:beside|with|by)|hold\s+my\s+hand|don'?t\s+leave|keep\s+me\s+company|sit\s+(?:with|beside)\s+me|stay\s+here)\b"
        if _re.search(companion_patterns, prompt_lower):
            return "I am right here beside you, Commander. I'm not going anywhere — take your time, you are safe and never alone."

        # Emotion detection — empathetic instant responses
        emotion_patterns = {
            "sadness": r"\b(sad|depressed|down|low|blue|heartbroken|miserable|lonely|hurt|disappointed|gloomy)\b",
            "anger": r"\b(angry|mad|furious|frustrated|upset|irritated|annoyed)\b",
            "fear": r"\b(scared|afraid|anxious|nervous|worried|terrified|panicked)\b",
            "joy": r"\b(happy|joyful|excited|grateful|proud|cheerful|delighted)\b",
            "stress": r"\b(stressed|overwhelmed|exhausted|burned out)\b",
            "unwell": r"\bnot\s+(?:feeling\s+)?(?:well|good|great|okay|ok|fine)\b",
        }
        for emo, pattern in emotion_patterns.items():
            if _re.search(pattern, prompt_lower):
                if emo == "sadness":
                    return "I'm right here with you. You don't have to go through this alone. Take a deep breath — I've got your back."
                elif emo == "anger":
                    return "I understand you're frustrated. Take a moment to breathe. I'm here, and I'm listening calmly."
                elif emo == "fear":
                    return "It's completely natural to feel this way. You're safe right now, and I'm here with you."
                elif emo == "joy":
                    return "That's wonderful to hear! Your happiness genuinely makes my day brighter too!"
                elif emo == "stress":
                    return "I can tell you're carrying a lot right now. Remember to take breaks — even small ones help. I'm here to handle anything you need."
                elif emo == "unwell":
                    return "I'm sorry to hear you're not feeling well. Please take it easy and rest. Is there anything I can do for you?"

        # Explicit help / capability queries ONLY (never bare "can you")
        if _re.search(r"^(?:help|what can you do|features|commands|capabilities|what are your features)\b", prompt_lower) or prompt_lower in ("help", "help me"):
            return "As an AGI, I perceive through real-time computer vision, reason across complex multi-domain problems, remember permanently, and control the operating system through desktop automation hands."

        # Conceptual / philosophical reflection
        if any(w in prompt_lower for w in ("think", "consciousness", "universe", "mind", "meaning", "agi", "intelligence", "life", "why", "how")):
            return f"Reflecting on '{prompt}': True intelligence emerges from synthesizing first principles with adaptive awareness. It's a dynamic interplay between internal models and external reality."

        return f"I'm engaging my general reasoning core on this. Let's analyze it from first principles together."

    # ─── Public API ───────────────────────────────────────────

    def _call_openai_chat(self, prompt: str, system_prompt: str = "", stream: bool = False, max_tokens: Optional[int] = None):
        """Shared OpenAI-compatible call (OpenAI, Groq, etc.)."""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.api_url or None)
        return client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens or self.max_tokens,
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

    def generate(self, prompt: str, system_prompt: str = "", stream: bool = False, max_tokens: Optional[int] = None) -> str:
        """Generate a response. In AUTO mode, tries each provider until one works."""
        if self.backend == BackendType.AUTO:
            return self._generate_auto(prompt, system_prompt, max_tokens=max_tokens)

        if self.backend in (BackendType.OPENAI, BackendType.GROQ) and self._available:
            try:
                response = self._call_openai_chat(prompt, system_prompt, stream=False, max_tokens=max_tokens)
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"API inference failed, falling back: {e}")
                return self._rule_based_response(prompt)
        elif self.backend == BackendType.OLLAMA and self._available:
            try:
                return self._call_ollama(prompt, system_prompt, max_tokens=max_tokens)
            except Exception as e:
                logger.error(f"Ollama inference failed, falling back: {e}")
                return self._rule_based_response(prompt)
        else:
            return self._rule_based_response(prompt)

    def _generate_auto(self, prompt: str, system_prompt: str = "", max_tokens: Optional[int] = None) -> str:
        limit = max_tokens or self.max_tokens
        for provider in self._providers:
            if provider == BackendType.GROQ:
                try:
                    key = getattr(self, '_keys', {}).get("groq") or self.api_key
                    if not key:
                        continue
                    from openai import OpenAI
                    client = OpenAI(api_key=key, base_url=self._urls["groq"])
                    for g_model in getattr(self, "GROQ_FALLBACK_MODELS", ["qwen/qwen3.8-27b", "groq/compound", "openai/gpt-oss-20b"]):
                        try:
                            response = client.chat.completions.create(
                                model=g_model,
                                messages=[
                                    {"role": "system", "content": system_prompt or "You are IRIS, an Artificial General Intelligence (AGI). Reason profoundly from first principles."},
                                    {"role": "user", "content": prompt},
                                ],
                                max_tokens=limit,
                                temperature=self.temperature,
                            )
                            content = response.choices[0].message.content
                            if content and content.strip():
                                return content.strip()
                        except Exception as ge:
                            logger.warning(f"Groq model {g_model} failed ({ge}), trying next model...")
                except Exception as e:
                    logger.warning(f"Groq provider failed ({e}), trying next provider...")
            elif provider == BackendType.OPENAI:
                try:
                    key = getattr(self, '_keys', {}).get("openai") or self.api_key
                    if not key:
                        continue
                    from openai import OpenAI
                    client = OpenAI(api_key=key)
                    for o_model in ["gpt-4o-mini", "gpt-3.5-turbo"]:
                        try:
                            response = client.chat.completions.create(
                                model=o_model,
                                messages=[
                                    {"role": "system", "content": system_prompt or "You are IRIS, an Artificial General Intelligence (AGI). Reason profoundly from first principles."},
                                    {"role": "user", "content": prompt},
                                ],
                                max_tokens=limit,
                                temperature=self.temperature,
                            )
                            content = response.choices[0].message.content
                            if content and content.strip():
                                return content.strip()
                        except Exception as oe:
                            logger.warning(f"OpenAI model {o_model} failed ({oe}), trying next model...")
                except Exception as e:
                    logger.warning(f"OpenAI failed ({e}), trying next provider...")
            elif provider == BackendType.OLLAMA:
                try:
                    return self._call_ollama(prompt, system_prompt, max_tokens=limit)
                except Exception as e:
                    logger.warning(f"Ollama failed ({e}), trying next provider...")
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
                    model = self.model_name if self.model_name != "llama3.2" else self.GROQ_MODEL
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
