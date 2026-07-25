"""
JarvisBrain — The central cognitive engine of the AI.

Architecture:
  Input → Analyze → Reason → Respond → Execute
  
Upgraded with F.R.I.D.A.Y.-inspired systems:
  - 27+ tools with LLM function-calling
  - Tool feedback loop with nuclear scrubber
  - Voice biometrics (MFCC speaker verification)
  - STT transcript cleaning + wake word detection
  - Window scanner + 4-strategy app launcher
  - Music library + YouTube search
  - Proactive engine (heartbeat, check-in, auto-sleep)
  - Message automation (WhatsApp/Email/Telegram)
  - Dynamic system prompt generator
  - Mode switching (Fast/Genius)
"""

import time
import logging
import threading
from typing import Optional, Callable, Any
from dataclasses import dataclass, field

logger = logging.getLogger("iris.brain")


@dataclass
class Thought:
    text: str
    timestamp: float = field(default_factory=time.time)
    confidence: float = 1.0
    context: dict = field(default_factory=dict)


@dataclass
class Action:
    type: str  # respond, execute, query, delegate, wait
    payload: Any = None
    priority: int = 0


class ThinkingPipeline:
    """The sequence of cognitive stages every input goes through."""

    STAGES = ["receive", "analyze", "contextualize", "reason", "decide", "respond"]

    def __init__(self):
        self.hooks: dict[str, list[Callable]] = {s: [] for s in self.STAGES}
        self._current_stage = None

    def register_hook(self, stage: str, fn: Callable):
        if stage in self.hooks:
            self.hooks[stage].append(fn)

    def execute(self, stage: str, data: Any) -> Any:
        self._current_stage = stage
        for hook in self.hooks[stage]:
            try:
                data = hook(data)
            except Exception as e:
                logger.error(f"Hook failed at stage {stage}: {e}")
        return data


class JarvisBrain:
    """
    The primary AI brain. Manages the thinking pipeline, personality,
    memory, voice, automation, and knowledge systems.
    
    Upgraded subsystems (F.R.I.D.A.Y.-inspired):
      - tools: 27+ LLM-callable tools (FS, system, memory, media, web)
      - tool_executor: Feedback loop + nuclear scrubber
      - voice_biometrics: MFCC speaker verification
      - stt: Transcript cleaning + wake word detection
      - window_manager: Window scanner + app launcher
      - music_library: Playlist and media management
      - proactive: Heartbeat, check-in, auto-sleep, timers
      - message_automation: WhatsApp/Email/Telegram
      - system_prompt: Dynamic system prompt generation
    """

    MODES = ("fast", "genius")

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.name = self.config.get("name", "Iris")
        self.owner = self.config.get("owner", "Sir")

        # Core subsystems (lazy-loaded)
        self._personality = None
        self._memory = None
        self._voice = None
        self._vision = None
        self._automation = None
        self._knowledge = None
        self._emotion = None
        self._replys = None
        self._api_keys = None

        # Upgraded subsystems
        self._tools = None
        self._tool_executor = None
        self._voice_biometrics = None
        self._stt = None
        self._wake_word = None
        self._window_manager = None
        self._app_launcher = None
        self._music_library = None
        self._proactive = None
        self._message_automation = None
        self._system_prompt = None

        # Mode
        self._mode = "genius"

        # Thinking pipeline
        self.pipeline = ThinkingPipeline()
        self._setup_pipeline_hooks()

        # State
        self.is_awake = True
        self.processing = False
        self.thought_log: list[Thought] = []

        # Event callbacks
        self.on_response: Optional[Callable] = None
        self.on_action: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

        # Thread safety
        self._lock = threading.Lock()
        self._thinking_thread: Optional[threading.Thread] = None

        logger.info(f"{self.name} initialized and ready.")

    def _setup_pipeline_hooks(self):
        self.pipeline.register_hook("receive", self._stage_receive)
        self.pipeline.register_hook("analyze", self._stage_analyze)
        self.pipeline.register_hook("contextualize", self._stage_contextualize)
        self.pipeline.register_hook("reason", self._stage_reason)
        self.pipeline.register_hook("decide", self._stage_decide)
        self.pipeline.register_hook("respond", self._stage_respond)

    def _stage_receive(self, data: dict) -> dict:
        """Clean and normalize input."""
        data["received_at"] = time.time()
        return data

    def _stage_analyze(self, data: dict) -> dict:
        """Analyze intent, sentiment, entities."""
        text = data["text"]
        lower = text.lower()

        # Intent detection
        if any(w in lower for w in ["open", "launch", "start"]):
            intent = "launch"
        elif any(w in lower for w in ["search", "find", "google", "look up"]):
            intent = "search"
        elif any(w in lower for w in ["remember", "save", "store", "note"]):
            intent = "remember"
        elif any(w in lower for w in ["who", "what", "when", "where", "why", "how", "tell me"]):
            intent = "query"
        elif any(w in lower for w in ["shutdown", "restart", "sleep"]):
            intent = "system"
        elif any(w in lower for w in ["create", "make", "write", "build", "new"]):
            intent = "create"
        elif any(w in lower for w in ["send", "email", "message", "text"]):
            intent = "communicate"
        elif any(w in lower for w in ["play", "music", "song", "video"]):
            intent = "media"
        elif any(w in lower for w in ["hello", "hi", "hey", "good"]):
            intent = "greeting"
        else:
            intent = "conversation"

        # Emotion analysis via dedicated module
        if self._emotion:
            emotion_result = self._emotion.analyze(text)
            sentiment = emotion_result["emotion"]
            data["emotion"] = emotion_result

            # Let emotion override intent for emotional contexts
            emotion_intent = self._emotion.get_intent_from_emotion(sentiment, emotion_result["intensity"])
            if emotion_intent != "conversation":
                intent = emotion_intent
        else:
            # Fallback basic sentiment
            sad_words = ["sad", "depressed", "unhappy", "lonely", "upset", "cry"]
            happy_words = ["happy", "great", "wonderful", "amazing", "excited", "love"]
            angry_words = ["angry", "furious", "mad", "annoyed", "frustrated"]
            sentiment = "neutral"
            if any(w in lower for w in sad_words):
                sentiment = "sad"
            if any(w in lower for w in happy_words):
                sentiment = "happy"
            if any(w in lower for w in angry_words):
                sentiment = "angry"

        data["intent"] = intent
        data["sentiment"] = sentiment
        data["analyzed_at"] = time.time()
        return data

    def _stage_contextualize(self, data: dict) -> dict:
        """Load relevant context and memory."""
        data["context"] = {
            "recent_history": self._memory.get_recent(5) if self._memory else [],
            "relevant_memories": self._memory.search(data["text"]) if self._memory else [],
            "timestamp": time.time(),
        }
        data["contextualized_at"] = time.time()
        return data

    def _stage_reason(self, data: dict) -> dict:
        """Generate reasoning and response plan."""
        intent = data["intent"]
        sentiment = data["sentiment"]
        text = data["text"]
        emotion_data = data.get("emotion")

        # Use dedicated replys module if available
        if self._replys:
            response = self._replys.generate(intent, text, sentiment, emotion_data)
        elif self._personality:
            # Fallback to personality-only responses
            responses = {
                "greeting": self._personality.greet(),
                "query": self._personality.respond_informative(text),
                "search": self._personality.respond_search(text),
                "launch": "Launching application...",
                "remember": "I'll remember that.",
                "system": self._personality.respond_system(text),
                "create": self._personality.respond_create(text),
                "communicate": "Preparing to send...",
                "media": "Playing media...",
                "conversation": self._personality.respond_conversation(text, sentiment),
            }
            response = responses.get(intent, self._default_response(text))
        else:
            response = self._default_response(text)

        data["reasoned_response"] = response
        data["reasoned_at"] = time.time()
        return data

    def _stage_decide(self, data: dict) -> Action:
        """Decide what to do — respond, execute, or both."""
        intent = data["intent"]
        text = data["text"]
        needs_execution = intent in ("launch", "system", "media", "search", "communicate", "create", "remember")
        return Action(
            type="execute" if needs_execution else "respond",
            payload={"text": data["reasoned_response"], "intent": intent, "original": text},
        )

    def _stage_respond(self, action: Action) -> dict:
        """Execute the decided action and produce final output."""
        text = action.payload.get("text", "")
        intent = action.payload.get("intent", "unknown")
        original = action.payload.get("original", "")
        self._log_thought(text)
        if action.type == "respond":
            if self.on_response:
                self.on_response(text)
        else:
            if self.on_action:
                self.on_action(action.payload)
        return {"text": text, "action": action.type, "intent": intent, "original": original}

    def _default_response(self, text: str) -> str:
        return f"I understand you said: {text}. How can I assist you further?"

    def _log_thought(self, text: str):
        thought = Thought(text=text)
        self.thought_log.append(thought)
        if len(self.thought_log) > 1000:
            self.thought_log.pop(0)

    # ─── Public API ───────────────────────────────────────────

    def think(self, text: str) -> dict:
        """
        Full thinking pipeline: input → response.
        This is the main entry point for all interactions.
        """
        if not self.is_awake:
            return {"text": "I am currently in standby mode. Please wake me first.", "action": "standby"}

        text = text.strip() if text else ""
        if not text:
            return {"text": "I didn't receive any input. How can I help you?", "action": "error", "intent": "unknown"}

        with self._lock:
            self.processing = True
            try:
                data = {"text": text}
                data = self.pipeline.execute("receive", data)
                data = self.pipeline.execute("analyze", data)
                data = self.pipeline.execute("contextualize", data)
                data = self.pipeline.execute("reason", data)
                action = self.pipeline.execute("decide", data)
                result = self.pipeline.execute("respond", action)
                return result
            except ValueError as e:
                logger.warning(f"Invalid input: {e}")
                return {"text": str(e), "action": "error"}
            except Exception as e:
                logger.error(f"Thinking failed: {e}", exc_info=True)
                if self.on_error:
                    self.on_error(str(e))
                return {"text": "I encountered an error while processing that.", "action": "error"}
            finally:
                self.processing = False

    def think_async(self, text: str, callback: Optional[Callable] = None):
        """Non-blocking think. Calls callback with result when done."""
        def _run():
            result = self.think(text)
            if callback:
                callback(result)
        self._thinking_thread = threading.Thread(target=_run, daemon=True)
        self._thinking_thread.start()

    def speak(self, text: str, preset: str = "default"):
        """Think and speak the response."""
        result = self.think(text)
        if self._voice and result["action"] != "error":
            self._voice.say(result["text"], preset=preset)
        return result

    def remember(self, key: str, value: Any):
        if self._memory:
            self._memory.store(key, value)

    def recall(self, key: str) -> Optional[Any]:
        if self._memory:
            return self._memory.retrieve(key)
        return None

    def wake(self):
        self.is_awake = True
        if self._proactive:
            self._proactive.set_sleeping(False)
        logger.info(f"{self.name} is now awake.")

    def sleep(self):
        self.is_awake = False
        if self._proactive:
            self._proactive.set_sleeping(True)
        logger.info(f"{self.name} is now in standby.")

    def set_mode(self, mode: str):
        if mode in self.MODES:
            self._mode = mode
            if self._system_prompt:
                self._system_prompt.set_mode(mode)
            logger.info(f"Mode set to: {mode}")

    def get_mode(self) -> str:
        return self._mode

    def status(self) -> dict:
        tool_count = self._tools.list_tools() if self._tools else 0
        return {
            "name": self.name,
            "awake": self.is_awake,
            "processing": self.processing,
            "mode": self._mode,
            "thoughts_logged": len(self.thought_log),
            "memory_available": self._memory is not None,
            "voice_available": self._voice is not None,
            "vision_available": self._vision is not None,
            "automation_available": self._automation is not None,
            "knowledge_available": self._knowledge is not None,
            "emotion_available": self._emotion is not None,
            "replys_available": self._replys is not None,
            "api_keys_loaded": self._api_keys.key_count() if self._api_keys else 0,
            "tools_loaded": tool_count,
            "tools": self._tools.get_status() if self._tools else None,
            "voice_biometrics": self._voice_biometrics.get_status() if self._voice_biometrics else None,
            "proactive": self._proactive.get_status() if self._proactive else None,
            "music_library": self._music_library.get_status() if self._music_library else None,
            "system_prompt": self._system_prompt.get_status() if self._system_prompt else None,
        }

    # ─── Subsystem injection ──────────────────────────────────

    def set_personality(self, personality):
        self._personality = personality

    def set_memory(self, memory):
        self._memory = memory

    def set_voice(self, voice):
        self._voice = voice

    def set_vision(self, vision):
        self._vision = vision

    def set_automation(self, automation):
        self._automation = automation

    def set_knowledge(self, knowledge):
        self._knowledge = knowledge

    def set_emotion(self, emotion):
        self._emotion = emotion

    def set_replys(self, replys):
        self._replys = replys
        if self._personality:
            self._replys.set_personality(self._personality)

    def set_api_keys(self, api_keys):
        self._api_keys = api_keys

    def set_tools(self, tools):
        self._tools = tools
        if self._memory:
            self._tools.set_memory_backend(self._memory)
        if self._system_prompt:
            self._system_prompt.set_tool_count(len(self._tools.list_tools()))

    def set_tool_executor(self, executor):
        self._tool_executor = executor

    def set_voice_biometrics(self, vb):
        self._voice_biometrics = vb

    def set_stt(self, stt):
        self._stt = stt

    def set_wake_word(self, ww):
        self._wake_word = ww

    def set_window_manager(self, wm):
        self._window_manager = wm

    def set_app_launcher(self, al):
        self._app_launcher = al

    def set_music_library(self, ml):
        self._music_library = ml
        if self._tools:
            self._tools.set_music_library(ml.get_all() if ml else [])

    def set_proactive(self, pe):
        self._proactive = pe

    def set_message_automation(self, ma):
        self._message_automation = ma

    def set_system_prompt(self, sp):
        self._system_prompt = sp
        self._system_prompt.set_mode(self._mode)
        if self._tools:
            self._system_prompt.set_tool_count(len(self._tools.list_tools()))
