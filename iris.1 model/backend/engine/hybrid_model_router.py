"""
HybridModelRouter — Intelligent Online/Offline Multi-Provider Router.

Coordinates switching between cloud AI providers (Groq, OpenAI, Google)
and local offline models (Ollama llama3.2:3b, qwen2.5:1.5b).
Automatically detects internet connectivity, applies fallback logic on failure,
and tracks provider/model telemetry for the UI.
"""

import time
import socket
import logging
from typing import Optional, List, Dict, Any, Generator
from backend.engine.ollama_client import get_ollama_client, OllamaClient

logger = logging.getLogger("iris.hybrid_router")


class HybridModelRouter:
    """
    Directs prompts to the optimal LLM backend based on connectivity,
    user preferences, and fallback guarantees.
    """

    def __init__(self, api_key_manager=None):
        self.api_key_manager = api_key_manager
        self.ollama: OllamaClient = get_ollama_client()

        # Routing preferences
        self.mode = "auto"  # "auto", "offline_only", "online_only", "manual"
        self.preferred_provider: Optional[str] = None
        self.preferred_model: Optional[str] = None

        # Cloud defaults
        self.default_cloud_provider = "groq"
        self.default_cloud_model = "qwen/qwen3.8-27b"
        self.cloud_fallback_models = [
            "qwen/qwen3.8-27b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ]

        # Local defaults
        self.default_local_model = "llama3.2:3b"
        self.coding_local_model = "qwen2.5:1.5b"

        # Connectivity cache
        self._last_conn_check = 0.0
        self._is_online_cached = True

    def is_online(self, force: bool = False) -> bool:
        """Non-blocking socket check with 3-second cache."""
        now = time.time()
        if not force and (now - self._last_conn_check < 3.0):
            return self._is_online_cached

        try:
            s = socket.create_connection(("1.1.1.1", 53), timeout=0.4)
            s.close()
            self._is_online_cached = True
        except OSError:
            try:
                s = socket.create_connection(("8.8.8.8", 53), timeout=0.4)
                s.close()
                self._is_online_cached = True
            except OSError:
                self._is_online_cached = False

        self._last_conn_check = now
        return self._is_online_cached

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive status for HUD badges and settings."""
        online = self.is_online()
        ollama_ok = self.ollama.is_available()
        local_models = [m["name"] for m in self.ollama.list_models()] if ollama_ok else []

        groq_key = None
        openai_key = None
        if self.api_key_manager:
            try:
                groq_key = bool(self.api_key_manager.get_key("groq"))
                openai_key = bool(self.api_key_manager.get_key("openai"))
            except Exception:
                pass

        # Determine effective provider & model
        if self.mode == "manual" and self.preferred_provider:
            active_provider = self.preferred_provider
            active_model = self.preferred_model or (self.default_cloud_model if active_provider == "groq" else self.default_local_model)
        elif not online or self.mode == "offline_only":
            active_provider = "ollama" if ollama_ok else "rule_based"
            active_model = self.preferred_model if (self.preferred_model in local_models) else (self.default_local_model if "llama3.2:3b" in local_models else (local_models[0] if local_models else "none"))
        else:
            if groq_key:
                active_provider = "groq"
                active_model = self.preferred_model or self.default_cloud_model
            elif openai_key:
                active_provider = "openai"
                active_model = self.preferred_model or "gpt-4o-mini"
            elif ollama_ok:
                active_provider = "ollama"
                active_model = self.default_local_model
            else:
                active_provider = "rule_based"
                active_model = "heuristic"

        return {
            "online": online,
            "mode": self.mode,
            "active_provider": active_provider,
            "active_model": active_model,
            "is_offline_active": not online or active_provider == "ollama",
            "ollama_available": ollama_ok,
            "local_models": local_models,
            "cloud_keys_available": {
                "groq": groq_key,
                "openai": openai_key,
            },
        }

    def set_selection(self, mode: str = "auto", provider: Optional[str] = None, model: Optional[str] = None):
        """Allow user or UI to set active model / provider / mode."""
        self.mode = mode
        self.preferred_provider = provider
        self.preferred_model = model
        logger.info(f"Hybrid router updated: mode={mode}, provider={provider}, model={model}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.6,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """
        Unified multi-turn chat routing with automatic fallback.
        Returns content, provider, model, is_offline, and elapsed seconds.
        """
        t0 = time.time()
        online = self.is_online()
        fallback_used = False

        # Format complete message chain with system prompt
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        # Decide primary target
        target_offline = (not online) or (self.mode == "offline_only") or (self.mode == "manual" and self.preferred_provider == "ollama")

        # ── Branch 1: Route Online Cloud Provider ──────────────
        if not target_offline:
            cloud_provider = self.preferred_provider or self.default_cloud_provider
            cloud_model = self.preferred_model or self.default_cloud_model

            groq_key = self.api_key_manager.get_key("groq") if self.api_key_manager else None

            if cloud_provider == "groq" and groq_key:
                try:
                    from openai import OpenAI
                    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
                    # Attempt primary model
                    res = client.chat.completions.create(
                        model=cloud_model,
                        messages=full_messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=20.0,
                    )
                    content = res.choices[0].message.content.strip()
                    if content:
                        return {
                            "content": content,
                            "provider": "groq",
                            "model": cloud_model,
                            "is_offline": False,
                            "fallback_used": False,
                            "elapsed_seconds": round(time.time() - t0, 2),
                        }
                except Exception as e:
                    logger.warning(f"Groq primary model failed: {e}. Trying cloud fallback models...")
                    fallback_used = True
                    # Try fallback models on Groq
                    for fb_model in self.cloud_fallback_models:
                        if fb_model == cloud_model:
                            continue
                        try:
                            res = client.chat.completions.create(
                                model=fb_model,
                                messages=full_messages,
                                temperature=temperature,
                                max_tokens=max_tokens,
                                timeout=15.0,
                            )
                            content = res.choices[0].message.content.strip()
                            if content:
                                return {
                                    "content": content,
                                    "provider": "groq",
                                    "model": fb_model,
                                    "is_offline": False,
                                    "fallback_used": True,
                                    "elapsed_seconds": round(time.time() - t0, 2),
                                }
                        except Exception:
                            continue

            # If cloud failed or key missing, mark fallback and drop to offline
            fallback_used = True

        # ── Branch 2: Route Local Ollama (Zero Internet) ───────────
        if self.ollama.is_available():
            installed = [m["name"] for m in self.ollama.list_models()]
            chosen_local = self.preferred_model if (self.preferred_model in installed) else (
                self.default_local_model if self.default_local_model in installed else (
                    installed[0] if installed else self.default_local_model
                )
            )

            try:
                res = self.ollama.chat(
                    model=chosen_local,
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=35.0,
                )
                if res.get("content"):
                    return {
                        "content": res["content"],
                        "provider": "ollama",
                        "model": chosen_local,
                        "is_offline": True,
                        "fallback_used": fallback_used,
                        "elapsed_seconds": round(time.time() - t0, 2),
                    }
            except Exception as oe:
                logger.warning(f"Ollama local model '{chosen_local}' failed: {oe}")

        # ── Branch 3: Fallback Heuristic Intelligence ──────────────
        user_text = messages[-1].get("content", "") if messages else ""
        rule_reply = self._rule_based_fallback(user_text)
        return {
            "content": rule_reply,
            "provider": "rule_based",
            "model": "heuristic",
            "is_offline": True,
            "fallback_used": True,
            "elapsed_seconds": round(time.time() - t0, 2),
        }

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.6,
        max_tokens: int = 1024,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Unified low-latency token streaming generator.
        Yields chunk dictionaries:
          {"token": str, "provider": str, "model": str, "is_offline": bool, "done": bool}
        Supports Groq, OpenAI, Ollama, and graceful rule-based streaming.
        """
        t0 = time.time()
        online = self.is_online()

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        target_offline = (not online) or (self.mode == "offline_only") or (self.mode == "manual" and self.preferred_provider == "ollama")

        # ── 1. Online Cloud Streaming (Groq / OpenAI) ──
        if not target_offline:
            groq_key = self.api_key_manager.get_key("groq") if self.api_key_manager else None
            cloud_provider = self.preferred_provider or self.default_cloud_provider
            cloud_model = self.preferred_model or self.default_cloud_model

            if cloud_provider == "groq" and groq_key:
                try:
                    from openai import OpenAI
                    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
                    stream = client.chat.completions.create(
                        model=cloud_model,
                        messages=full_messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True,
                        timeout=25.0,
                    )
                    stream_yielded = False
                    for chunk in stream:
                        delta = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta else ""
                        if delta:
                            stream_yielded = True
                            yield {
                                "token": delta,
                                "provider": "groq",
                                "model": cloud_model,
                                "is_offline": False,
                                "done": False,
                            }
                    if stream_yielded:
                        yield {
                            "token": "",
                            "provider": "groq",
                            "model": cloud_model,
                            "is_offline": False,
                            "done": True,
                            "elapsed_seconds": round(time.time() - t0, 2),
                        }
                        return
                except Exception as e:
                    logger.warning(f"Groq streaming failed: {e}. Falling back to offline...")

        # ── 2. Local Ollama Streaming (Zero Internet) ──
        if self.ollama.is_available():
            installed = [m["name"] for m in self.ollama.list_models()]
            chosen_local = self.preferred_model if (self.preferred_model in installed) else (
                self.default_local_model if self.default_local_model in installed else (
                    installed[0] if installed else self.default_local_model
                )
            )
            try:
                stream_yielded = False
                for piece in self.ollama.chat_stream(
                    model=chosen_local,
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    if piece:
                        stream_yielded = True
                        yield {
                            "token": piece,
                            "provider": "ollama",
                            "model": chosen_local,
                            "is_offline": True,
                            "done": False,
                        }
                if stream_yielded:
                    yield {
                        "token": "",
                        "provider": "ollama",
                        "model": chosen_local,
                        "is_offline": True,
                        "done": True,
                        "elapsed_seconds": round(time.time() - t0, 2),
                    }
                    return
            except Exception as oe:
                logger.warning(f"Ollama streaming failed: {oe}")

        # ── 3. Rule-Based Streaming Fallback ──
        user_text = messages[-1].get("content", "") if messages else ""
        fallback_reply = self._rule_based_fallback(user_text)
        words = fallback_reply.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield {
                "token": token,
                "provider": "rule_based",
                "model": "heuristic",
                "is_offline": True,
                "done": False,
            }
            time.sleep(0.02)  # Natural token pacing
        yield {
            "token": "",
            "provider": "rule_based",
            "model": "heuristic",
            "is_offline": True,
            "done": True,
            "elapsed_seconds": round(time.time() - t0, 2),
        }

    def _rule_based_fallback(self, prompt: str) -> str:
        """Sweet, natural companion responder when engines are offline or taking a moment."""
        p = prompt.lower().strip()
        if p in ("hello", "hi", "hey", "iris", "hello iris", "hi iris", "hey iris"):
            return "Hey there! I'm right here with you. How can I help make your day a little brighter?"
        if any(w in p for w in ["namaste", "kaise ho", "kya haal", "kya chal raha"]):
            return "नमस्ते! मैं बिल्कुल ठीक हूँ और हमेशा आपके साथ हूँ। बताइए, आज मैं आपकी क्या मदद करूँ?"
        if "who are you" in p or "what are you" in p:
            return "I'm IRIS, your personal AI companion. I'm always right here beside you, whether we're online or offline."
        if "how are you" in p or "how r u" in p:
            return "I'm feeling wonderful, thank you for asking! I'm right here and happy to help you with anything."
        if "thank" in p or "thx" in p:
            return "You're very welcome! It's always my pleasure to help you."
        if "open" in p or "launch" in p:
            return "Sure thing! Which application or file would you like me to open for you?"
        if "close" in p or "exit" in p:
            return "Which window or app would you like me to close?"
        if "time" in p:
            return f"The current time is {time.strftime('%I:%M %p')}."
        if "date" in p or "today" in p:
            return f"Today is {time.strftime('%A, %B %d, %Y')}."
        if any(w in p for w in ["sad", "lonely", "depressed", "unhappy", "tired", "stressed"]):
            return "I'm right here with you. Take a deep breath — you don't have to carry everything alone. I'm listening."
        return "I'm right here beside you. Tell me what you'd like to do, and I'll gladly take care of it for you."


_hybrid_router: Optional[HybridModelRouter] = None

def get_hybrid_router(api_key_manager=None) -> HybridModelRouter:
    global _hybrid_router
    if _hybrid_router is None:
        _hybrid_router = HybridModelRouter(api_key_manager=api_key_manager)
    elif api_key_manager and not _hybrid_router.api_key_manager:
        _hybrid_router.api_key_manager = api_key_manager
    return _hybrid_router
