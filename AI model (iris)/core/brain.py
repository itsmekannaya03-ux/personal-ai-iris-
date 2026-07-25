import logging
import threading
import time
from typing import Optional, Callable, Any
from dataclasses import dataclass, field

logger = logging.getLogger("igris.core.brain")


@dataclass
class Thought:
    text: str
    confidence: float = 1.0
    intent: str = "unknown"
    timestamp: float = field(default_factory=time.time)
    context: dict = field(default_factory=dict)


@dataclass
class Action:
    type: str = "respond"
    payload: dict = field(default_factory=dict)
    priority: int = 0
    requires_confirmation: bool = False


class ThinkingPipeline:
    STAGES = ["receive", "analyze", "contextualize", "reason", "decide", "respond"]

    def __init__(self):
        self._hooks: dict[str, list] = {s: [] for s in self.STAGES}

    def register_hook(self, stage: str, fn: Callable):
        if stage in self._hooks:
            self._hooks[stage].append(fn)

    def execute(self, stage: str, data: dict) -> dict:
        for hook in self._hooks.get(stage, []):
            data = hook(data)
        return data


class IrisBrain:
    MODES = {"fast", "genius"}

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.name = self.config.get("name", "Iris")
        self.is_awake = True
        self.processing = False
        self._mode = "genius"
        self._lock = threading.Lock()
        self._thinking_thread: Optional[threading.Thread] = None

        self.pipeline = ThinkingPipeline()
        self.thought_log: list[Thought] = []
        self._wire_default_pipeline()

        # External subsystem references (injected after init)
        self._intent: Any = None
        self._decider: Any = None
        self._personality: Any = None
        self._model_router: Any = None
        self._memory: Any = None
        self._voice: Any = None
        self._vision: Any = None
        self._hands: Any = None

        self.on_response: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

        logger.info(f"{self.name} brain initialized")

    def _wire_default_pipeline(self):
        self.pipeline.register_hook("receive", self._stage_receive)
        self.pipeline.register_hook("analyze", self._stage_analyze)
        self.pipeline.register_hook("contextualize", self._stage_contextualize)
        self.pipeline.register_hook("reason", self._stage_reason)
        self.pipeline.register_hook("decide", self._stage_decide)
        self.pipeline.register_hook("respond", self._stage_respond)

    def _stage_receive(self, data: dict) -> dict:
        data["timestamp"] = time.time()
        data["mode"] = self._mode
        return data

    def _stage_analyze(self, data: dict) -> dict:
        if self._intent:
            result = self._intent.analyze(data["text"])
            data.update(result)
        else:
            data["intent"] = "unknown"
            data["confidence"] = 0.0
        return data

    def _stage_contextualize(self, data: dict) -> dict:
        if self._memory:
            context = self._memory.recall_relevant(data["text"])
            data["context"] = context
        else:
            data["context"] = {}
        return data

    def _stage_reason(self, data: dict) -> dict:
        if self._model_router:
            response = self._model_router.generate(
                prompt=data["text"],
                intent=data.get("intent", "unknown"),
                context=data.get("context", {}),
                mode=self._mode,
            )
            data["response"] = response
        else:
            data["response"] = self._fallback_response(data["text"])
        return data

    def _stage_decide(self, data: dict) -> dict:
        data["action"] = Action(type="respond", payload={"text": data.get("response", "")})
        if self._decider:
            decision = self._decider.decide(data)
            data["action"] = decision
        return data

    def _stage_respond(self, data: dict) -> dict:
        action = data.get("action", Action())
        text = action.payload.get("text", "")
        if self._personality:
            text = self._personality.apply(text, data.get("intent", "unknown"))
        thought = Thought(text=data["text"], intent=data.get("intent", "unknown"))
        self.thought_log.append(thought)
        if len(self.thought_log) > 100:
            self.thought_log.pop(0)

        result = {"text": text, "action": action.type, "intent": data.get("intent", "unknown")}
        if action.type != "respond" and "payload" in action.payload:
            result["execution"] = action.payload
        return result

    def _fallback_response(self, text: str) -> str:
        return f"I understand you said: '{text}'. I'm running in fallback mode — connect a model backend for full capability."

    # ─── Public API ───────────────────────────────────────────

    def think(self, text: str) -> dict:
        if not self.is_awake:
            return {"text": "I am in standby. Please wake me first.", "action": "standby", "intent": "unknown"}
        text = text.strip() if text else ""
        if not text:
            return {"text": "I didn't receive any input.", "action": "error", "intent": "unknown"}
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
            except Exception as e:
                logger.error(f"Think failed: {e}", exc_info=True)
                if self.on_error:
                    self.on_error(str(e))
                return {"text": "I encountered an error.", "action": "error", "intent": "unknown"}
            finally:
                self.processing = False

    def think_async(self, text: str, callback: Optional[Callable] = None):
        def _run():
            result = self.think(text)
            if callback:
                callback(result)
        self._thinking_thread = threading.Thread(target=_run, daemon=True)
        self._thinking_thread.start()

    def wake(self):
        self.is_awake = True
        logger.info(f"{self.name} is awake.")

    def sleep(self):
        self.is_awake = False
        logger.info(f"{self.name} is in standby.")

    def set_mode(self, mode: str):
        if mode in self.MODES:
            self._mode = mode
            logger.info(f"Mode set to {mode}")

    def get_mode(self) -> str:
        return self._mode

    def status(self) -> dict:
        return {
            "name": self.name,
            "awake": self.is_awake,
            "processing": self.processing,
            "mode": self._mode,
            "thoughts_logged": len(self.thought_log),
            "intent_available": self._intent is not None,
            "decider_available": self._decider is not None,
            "personality_available": self._personality is not None,
            "model_router_available": self._model_router is not None,
            "memory_available": self._memory is not None,
            "voice_available": self._voice is not None,
            "vision_available": self._vision is not None,
            "hands_available": self._hands is not None,
        }

    # ─── Subsystem injection ──────────────────────────────────

    def set_intent(self, intent): self._intent = intent
    def set_decider(self, decider): self._decider = decider
    def set_personality(self, personality): self._personality = personality
    def set_model_router(self, router): self._model_router = router
    def set_memory(self, memory): self._memory = memory
    def set_voice(self, voice): self._voice = voice
    def set_vision(self, vision): self._vision = vision
    def set_hands(self, hands): self._hands = hands
