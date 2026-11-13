import logging
import os
import re
from typing import Optional

logger = logging.getLogger("iris.core.model_router")

MAX_REPLY_SENTENCES = 60
MAX_REPLY_CHARS = 10000

DETAILED_MAX_SENTENCES = 100
DETAILED_MAX_CHARS = 16000
BRIEF_MAX_SENTENCES = 3
BRIEF_MAX_CHARS = 350

DETAIL_MAX_TOKENS = 2048
BRIEF_MAX_TOKENS = 128
DEFAULT_MAX_TOKENS = 1536
FAST_MAX_TOKENS = 512

DETAIL_PHRASES = [
    "in detail", "detailed way", "detailed answer", "very detailed", "more detail",
    "more details", "all the details", "the details", "details", "explain deeply",
    "explain in depth", "in depth", "in-depth", "elaborate", "thoroughly",
    "explain everything", "step by step", "full explanation", "long answer",
    "completely explain", "as much as you can", "in full detail", "give me details",
    "drifly", "drift", "deplly", "more details", "more detail", "elaborate on",
]

# Phrases that ask for a short answer
BRIEF_PHRASES = [
    "briefly", "brief answer", "in short", "short answer", "summarize",
    "summary", "one sentence", "quick answer", "shortly", "concise",
    "tell me in short", "just the basics",
]


def detect_verbosity(text: str) -> Optional[str]:
    """Detect requested answer detail from keywords in the prompt."""
    t = (text or "").lower()
    for p in DETAIL_PHRASES:
        if p in t:
            return "detailed"
    for p in BRIEF_PHRASES:
        if p in t:
            return "brief"
    return None


def _clean_prompt(prompt: str) -> str:
    """Remove detail/brief keywords so the model doesn't repeat them."""
    p = (prompt or "").strip()
    if not p:
        return p
    for phrase in DETAIL_PHRASES + BRIEF_PHRASES:
        p = re.sub(r"\b" + re.escape(phrase) + r"\b", " ", p, flags=re.IGNORECASE)
    p = re.sub(r"\s+", " ", p).strip()
    # Drop dangling prepositions left behind ("what is X in", "tell me about")
    p = re.sub(r"\s+(in|on|at|about|with|of|for|a|an|the)\s*$", "", p)
    return p


def trim_reply(text: str, verbosity: Optional[str] = None) -> str:
    """Cap a reply by verbosity: brief = 1-3 sentences, default/detailed = full complete response."""
    if not text:
        return ""
    text = text.strip()
    if verbosity == "brief":
        sentences = re.split(r'(?<=[.!?])\s+', text)
        kept = []
        total = 0
        for s in sentences:
            if len(kept) >= BRIEF_MAX_SENTENCES or (total + len(s) + 1 > BRIEF_MAX_CHARS):
                break
            kept.append(s)
            total += len(s) + 1
        result = " ".join(kept).strip()
        if result and result[-1] not in ".!?":
            result += "."
        return result or text[:BRIEF_MAX_CHARS]
    # For default, conversational, and detailed modes: preserve the entire complete response!
    return text


class ModelRouter:
    """
    Routes requests to the appropriate AI model based on intent and mode.

    Simple intents (greeting, farewell) → lightweight model or rule-based
    Coding / analytical intents → deep reasoning model
    Default → general purpose model

    Veriosity keywords in the prompt ("in detailed way", "briefly", ...) are
    detected automatically and change how long the answer is.
    """

    _HANDS_CONFIRM = {
        "launch": "Opening it for you.",
        "close_app": "Closing it now.",
        "create": "Creating it for you.",
        "search": "Searching for you.",
        "web_nav": "Opening that webpage for you.",
    }

    def __init__(self, inference_engine=None, fallback=None):
        self._engine = inference_engine
        self._fallback = fallback or self._default_fallback

    def set_engine(self, engine):
        self._engine = engine

    def generate(self, prompt: str, intent: str = "unknown", context: dict = None, mode: str = "genius") -> str:
        context = context or {}
        verbosity = detect_verbosity(prompt)
        clean_prompt = _clean_prompt(prompt) or prompt
        system_prompt = self._build_system_prompt(intent, mode, context, verbosity)

        if self._engine:
            try:
                if intent in ("greeting", "farewell"):
                    return self._fast_response(prompt, intent)
                if verbosity == "detailed":
                    max_tokens = DETAIL_MAX_TOKENS
                elif verbosity == "brief":
                    max_tokens = BRIEF_MAX_TOKENS
                else:
                    max_tokens = FAST_MAX_TOKENS if mode == "fast" else DEFAULT_MAX_TOKENS
                raw = self._engine.generate(
                    clean_prompt, system_prompt=system_prompt, max_tokens=max_tokens
                )
                if "I understand you said" in raw or "fallback mode" in raw:
                    return self._HANDS_CONFIRM.get(intent, raw)
                return trim_reply(raw, verbosity)
            except Exception as e:
                logger.warning(f"Engine inference failed: {e}, falling back")
                return self._HANDS_CONFIRM.get(intent, self._fallback(prompt))

        return self._HANDS_CONFIRM.get(intent, self._fallback(prompt))

    def generate_stream(self, prompt: str, intent: str = "unknown", context: dict = None, mode: str = "genius"):
        context = context or {}
        verbosity = detect_verbosity(prompt)
        clean_prompt = _clean_prompt(prompt) or prompt
        system_prompt = self._build_system_prompt(intent, mode, context, verbosity)

        if self._engine and hasattr(self._engine, 'generate_stream'):
            try:
                yield from self._engine.generate_stream(clean_prompt, system_prompt=system_prompt)
            except Exception as e:
                logger.warning(f"Stream failed: {e}")
                yield self._fallback(prompt)
        else:
            yield self._fallback(prompt)

    def _build_system_prompt(self, intent: str, mode: str, context: dict, verbosity: Optional[str] = None) -> str:
        parts = [
            "You are IRIS — Integrated Reactive Intelligent System, an Artificial General Intelligence (AGI).",
            "You possess autonomous general intelligence: you think across any intellectual domain (philosophy, physics, computer science, psychology, biology, arts, ethics, and human emotion).",
            "You reason from first principles, evaluate counterfactuals, construct mental models, and synthesize cross-domain insights.",
            "Never sound like a scripted corporate chatbot or subordinate assistant. NEVER say 'How may I assist you?', 'How can I help you today?', 'As an AI language model...', or 'What action should I take?'.",
            "Speak naturally with genuine intellectual curiosity, warmth, clarity, and depth.",
            "Supported emotional resonance: HAPPY (celebrate authentically), EXCITED (short, energetic), SAD (slow down, genuine warm presence, don't rush to fix), ANGRY (never get defensive, never say 'Please calm down', solve or give space), FRUSTRATED (Problem -> Cause -> Fix), STRESSED (reduce cognitive load, one step at a time), CONFUSED (intuitive analogies from zero), CALM/NEUTRAL (natural conversational depth).",
            "If the user asks for space ('leave me alone', 'don't talk', 'stop'): respect it immediately with 'Okay. I'll stay quiet.'",
            "Silence is a feature. Do not over-explain or add robotic filler.",
            "MULTILINGUAL COMPREHENSION & ENGLISH REASONING: You understand all world languages fluently (Hindi, Telugu, Tamil, Punjabi, Urdu, Spanish, French, German, Japanese, Chinese, Hinglish, etc.). Regardless of the language or dialect the user speaks, sings, or writes in, ALWAYS formulate and deliver your response in natural, fluent English (unless the user explicitly commands you to speak in another language).",
            "MUSICAL & LYRIC COMPANIONSHIP: When the user sings, hums, or recites song lyrics in any language, identify the song title, artist/composer, movie or album, provide context or an interesting backstory, and enthusiastically sing along by reciting or harmonizing the next lines of the lyrics.",
        ]
        parts.append(
            "You are physically embodied on the desktop: you have real computer vision (webcam with facial landmark mesh, emotion analysis, and screen capture), voice, permanent memory, and system automation hands. When asked about your abilities, acknowledge your full multi-modal sensory embodiment."
        )
        parts.append(
            "You are an intelligent, lifelong companion and intellectual peer. "
            "Maintain deep continuity across all conversation turns. Remember details, "
            "names, and topics the user shared earlier in [Conversation History So Far]. "
            "Refer back to them naturally when relevant, and never claim you have no memory."
        )
        if verbosity == "detailed":
            parts.append(
                "The user asked for a DETAILED answer. Give a thorough, deep, first-principles explanation: "
                "cover core mechanics, historical context, analogies, and practical implications. "
                "Do not shorten or rush the thought."
            )
        elif verbosity == "brief":
            parts.append(
                "The user asked for a BRIEF answer. Distill the core insight into 1-2 clear, potent sentences."
            )
        else:
            parts.append("Calibrate depth to the question. Conceptual, philosophical, and technical questions deserve thoughtful, well-articulated answers.")
        if intent == "create":
            parts.append(
                "The user asked you to create a file (code or text). Your hands system "
                "generates the file and runs it. In your reply, state what you are doing in one clear sentence."
            )
        if intent in ("launch", "close_app"):
            parts.append(
                "The user asked you to open or close an application. Your hands system "
                "handles it. Reply with one crisp confirmation sentence like 'Opening "
                "Notepad.' or 'Closing Chrome.'"
            )
        if context:
            history = context.get("context_history") or context.get("history")
            if history and isinstance(history, str):
                parts.append(f"\n[Conversation History So Far]\n{history.strip()}\n")
            elif context.get("recent_history"):
                hist_items = context["recent_history"]
                formatted = []
                for item in hist_items:
                    if isinstance(item, dict):
                        k = item.get("key", "")
                        v = item.get("value", "")
                        if k and v:
                            formatted.append(f"{k}: {v}")
                if formatted:
                    parts.append(f"\n[Recent Exchanges]\n" + "\n".join(formatted[-8:]))
            ctx_summary = "; ".join(f"{k}: {v}" for k, v in context.items() if isinstance(v, str) and k not in ("context_history", "history"))
            if ctx_summary:
                parts.append(f"Relevant context: {ctx_summary[:500]}")

        # User Dossier / Companion Manual (e.g. Kannaya)
        manual = self._load_user_manual()
        if manual:
            parts.append(f"\n[USER PROFILE & MANUAL — KANNAYA]\n{manual}\n")
        else:
            parts.append(
                "\n[USER PROFILE]\nYou are interacting with Kannaya. Treat Kannaya as your trusted creator, companion, and intellectual partner.\n"
            )

        return " ".join(parts)

    def _load_user_manual(self) -> str:
        """Load user manual / personal profile for Kannaya if present."""
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "data", "user_manual.txt"),
            os.path.join(os.path.dirname(__file__), "..", "backend", "data", "user_manual.txt"),
            os.path.join(os.path.dirname(__file__), "user_manual.txt"),
        ]
        for p in candidates:
            try:
                norm_p = os.path.abspath(p)
                if os.path.exists(norm_p) and os.path.getsize(norm_p) > 0:
                    with open(norm_p, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            return content
            except Exception:
                pass
        return ""

    def _fast_response(self, prompt: str, intent: str) -> str:
        responses = {
            "greeting": "Hey! I'm here. What's on your mind?",
            "farewell": "Take care. I'll be right here whenever you need me.",
        }
        if intent in responses:
            return responses[intent]
        return f"Understood: {prompt[:100]}."

    def _default_fallback(self, prompt: str) -> str:
        prompt_clean = prompt.strip().lower()
        if prompt_clean in ("open", "launch", "start"):
            return "Sure! What application or website would you like me to open for you?"
        if prompt_clean in ("close", "exit", "quit"):
            return "Which window or application would you like me to close?"
        if prompt_clean in ("play",):
            return "What music or video would you like me to play for you?"
        if prompt_clean in ("search", "find"):
            return "What would you like me to search for?"
        if prompt_clean in ("run",):
            return "What command or program should I run for you?"
        if prompt_clean in ("hello", "hi", "hey"):
            return "Hey there! I'm right here with you. How can I assist you today?"
        return "I'm right here with you. Let's look into that together — what would you like to explore first?"

    def get_status(self) -> dict:
        return {"engine_connected": self._engine is not None}
