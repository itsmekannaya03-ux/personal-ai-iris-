"""
IRIS Engine API — FastAPI REST interface for the AI engine.

Frontend-facing endpoints (proxied from the frontend at /api/*):
  POST /chat                  -> {"response": str}  (speaks when voice=true)
  GET  /status                -> engine status
  GET  /memory                -> memory stats
  GET  /memory/stats          -> memory layer stats
  POST /memory/store          -> store a memory
  GET  /memory/recall/{key}   -> recall a memory
  GET  /system                -> system info
  GET  /conversation/status   -> token usage + session state
  POST /conversation/new-session
  GET  /conversation/summary
  POST /conversation/max-tokens

Vision system:
  GET  /vision/status         -> camera/screenshot/OCR/face availability
  POST /vision/see            -> screenshot + AI description (Gemini/OpenRouter)
  POST /vision/camera         -> webcam photo + AI description
  POST /vision/faces          -> face count on the latest camera photo
  POST /vision/ui             -> UI elements found on the screen
  POST /vision/scan           -> scan a folder with the file scanner

Audio system:
  GET  /audio/status          -> microphone devices
  POST /audio/listen          -> record N seconds + transcribe (Groq Whisper)

Automation system:
  GET  /automation/status     -> hands subsystems ready
  POST /automation/launch     -> launch an app (e.g. {"app": "notepad"})
  POST /automation/run-command-> safe terminal command

Diagnostics:
  GET  /test/all              -> run a full test of every system
"""

import logging
import time
import os
import uuid
import base64
import json
import tempfile
import wave
import re
import threading
import asyncio
import subprocess
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from backend.audio.silero_vad import get_silero_vad
from backend.audio.noise_suppressor import get_noise_suppressor
from backend.engine.barge_in_manager import get_barge_in_manager
from backend.engine.streaming_orchestrator import get_streaming_orchestrator
from backend.audio.full_duplex_session import FullDuplexAudioSession, create_or_get_session, remove_session, get_all_sessions_status

logger = logging.getLogger("iris.api")


class ChatRequest(BaseModel):
    message: str
    voice: Optional[bool] = True
    voice_preset: Optional[str] = None
    is_voice: Optional[bool] = False
    conversation_id: Optional[str] = None
    person_name: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    processing_time: Optional[float] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    is_offline: Optional[bool] = False
    conversation_id: Optional[str] = None



class MemoryStoreRequest(BaseModel):
    key: str
    value: str


class MemoryRecallRequest(BaseModel):
    key: str


class VoiceSayRequest(BaseModel):
    text: str
    preset: Optional[str] = None


class MaxTokensRequest(BaseModel):
    max_tokens: int


class NewSessionRequest(BaseModel):
    keep_summary: Optional[bool] = True


class VisionScanRequest(BaseModel):
    folder: Optional[str] = None
    depth: Optional[int] = 0


class LaunchRequest(BaseModel):
    app: str
    args: Optional[str] = ""


class CommandRequest(BaseModel):
    command: str


class PresenceEnrollRequest(BaseModel):
    name: Optional[str] = "Commander"


class PresenceToggleRequest(BaseModel):
    enable: Optional[bool] = None


class SimulateEmotionRequest(BaseModel):
    emotion: str = "sad"


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


_NO_CONTENT_MARKER = "I cannot see anything clearly"


def _is_blank_frame(image_path: str, mean_thresh: float = 20.0, edge_thresh: float = 0.005) -> bool:
    """True if the image is essentially dark/uniform — a covered lens,
    a black screen, or a pitch-dark view. Vision LLMs hallucinate text
    on such frames, so we detect them locally first."""
    try:
        import cv2
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return False
        if float(img.mean()) > mean_thresh:
            return False
        edges = cv2.Canny(img, 50, 150)
        edge_ratio = float((edges > 0).sum()) / edges.size
        return edge_ratio < edge_thresh
    except Exception:
        return False


def _frame_quality(image_path: str, blur_thresh: float = 150.0) -> str:
    """Classify a captured image locally: 'blank' (dark/uniform), 'blurry', or 'ok'.

    This runs BEFORE any AI is called, so Iris never hallucinates content
    from a dark, covered, or out-of-focus frame."""
    try:
        import cv2
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return "blank"
        h, w = img.shape[:2]
        mean = float(img.mean())
        edges = cv2.Canny(img, 50, 150)
        edge_ratio = float((edges > 0).sum()) / edges.size
        if mean <= 20.0 and edge_ratio < 0.005:
            return "blank"
        small = cv2.resize(img, (320, int(h * 320 / max(w, 1))))
        laplacian_var = float(cv2.Laplacian(small, cv2.CV_64F).var())
        if laplacian_var < blur_thresh:
            return "blurry"
        return "ok"
    except Exception:
        return "ok"


_CONFIRM_WORDS = {
    "yes", "yeah", "yep", "sure", "ok", "okay", "alright", "confirm", "go ahead",
    "do it", "fine", "approve", "approved", "approve it", "i approve", "proceed", "thumbs up", "👍"
}

_FAST_PATTERNS = [
    (["hello", "hi ", "hey", "hi!", "hello!", "good morning", "good evening", "good afternoon", "howdy", "yo",
      "hello iris", "hi iris", "hey iris"],
     "Hey! Ready when you are."),
    (["thank", "thanks", "thank you", "thx", "appreciated"],
     "Anytime 👍"),
    (["bye", "goodbye", "see you", "good night", "goodnight", "see ya"],
     "Later! I'll be around."),
    (["are you there", "are you alive", "are you awake", "you there", "hello?"],
     "Right here with you."),
    (["yes", "yeah", "ok", "okay", "sure", "alright"],
     "👍"),
]


_CODE_REQUEST = re.compile(
    r"\b(write|create|make|generate|build|script|program|code|function|print|import|class|letter|poem|essay)\b",
    re.IGNORECASE,
)


def _fast_reply(message: str) -> Optional[str]:
    """Instant rule-based reply for common phrases and half-sentences — response in under 1ms.

    Phrases are matched on word boundaries, and anything that looks like a
    code/text-generation request skips the fast replies entirely (so
    "print hello world" never gets answered with a greeting)."""
    m = message.lower().strip()

    # Space & Silence requests — ALWAYS forward to brain
    if re.search(r"\b(leave me alone|don't talk|dont talk|need space|give me space|stop talking|be quiet|stay quiet|not now|shut up|want to be alone|wanna be alone)\b|^stop$|^nothing$", m):
        return None

    # Emotion & Companion detection — ALWAYS forward to brain for empathetic responses
    if re.search(r"\b(?:(?:yes|yeah)\s+)?(?:i(?:'m|m|\s+am|\s+feel|\s+feeling)|feeling|felt|am)\s+(?:so\s+|very\s+|really\s+|just\s+)?(?:sad|happy|angry|mad|upset|frustrated|depressed|anxious|nervous|scared|worried|lonely|bored|tired|exhausted|stressed|excited|grateful|thankful|confused|lost|overwhelmed|hurt|disappointed|furious|heartbroken|miserable|joyful|cheerful|delighted|gloomy|down|low|blue|afraid|terrified|annoyed|irritated)\b", m):
        return None
    if re.search(r"\b(?:i(?:'m|m|\s+am)\s+not\s+(?:feeling\s+)?(?:well|good|great|okay|ok|fine|alright))\b", m):
        return None
    if re.search(r"\b(?:sad|sadness|depressed|heartbroken|lonely|miserable|crying|tears|unhappy|stay\s+(?:beside|with|by)|be\s+with\s+me|beside\s+(?:of\s+)?me|keep\s+me\s+company|hold\s+(?:my\s+)?hand|don't\s+leave|dont\s+leave|comfort\s+me)\b", m):
        return None
    # Emotional longing, love, affection, relationships, desire for connection, specific dialogue
    if re.search(r"\b(?:love|someone\s+to\s+love|someone\s+love\s+me|be\s+loved|want\s+love|need\s+love|unloved|hug\s+me|hold\s+me|care\s+about\s+me|do\s+you\s+love\s+me|want\s+someone|need\s+someone|alone|dating|girlfriend|boyfriend|partner|messed\s+up|tired|stupid\s+thing|finally|working|idea\s+for\s+iris)\b", m):
        return None

    # Long-term memory & personal facts — ALWAYS forward to brain
    if re.search(r"\b(remember|recall|my name|who am i|favorite|what is my|do you know me|what did i)\b", m):
        return None

    # Immediate handling of solitary command verbs / half-sentences
    if m in ("open", "launch", "start", "opn"):
        return "What application or website would you like me to open?"
    if m in ("close", "exit", "quit"):
        return "Which application or window would you like me to close?"
    if m in ("search", "find", "google"):
        return "What would you like me to search for?"
    if m in ("play",):
        return "What music or video would you like me to play?"
    if m in ("run",):
        return "What command or program should I run for you?"
    if m in ("create", "make"):
        return "What file or folder would you like me to create?"
    if m in ("delete", "remove"):
        return "What file or item should I delete?"

    if _CODE_REQUEST.search(m):
        return None

    # Only apply fast replies to short standalone greetings or confirmations (1-4 words).
    # Compound thoughts or sentences MUST be processed by the AGI Brain!
    if len(m.split()) > 4:
        return None

    _CONFIRM_SET = {"yes", "yeah", "ok", "okay", "sure", "alright"}
    for phrases, reply in _FAST_PATTERNS:
        # EXACT match is required for single-word confirmations/acknowledgments
        if m in phrases:
            return reply
        for p in phrases:
            p_clean = p.strip()
            # NEVER substring-match single confirmation words across full sentences
            if p_clean in _CONFIRM_SET:
                continue
            if len(p_clean) >= 4 and re.search(rf"\b{re.escape(p_clean)}\b", m):
                return reply
    return None


class ConversationSession:
    """Persistent long-term conversation session manager with rolling context & summaries."""

    def __init__(self, max_tokens: int = 8192, session_file: Optional[str] = None):
        self.max_tokens = max_tokens
        self.messages: list[dict] = []
        self.summary: Optional[str] = None
        self._file = session_file or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chat_session.json")
        self._load()

    def _load(self):
        try:
            if os.path.exists(self._file):
                with open(self._file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.messages = data.get("messages", [])[-100:]
                    self.summary = data.get("summary")
        except Exception:
            pass

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self._file), exist_ok=True)
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump({"messages": self.messages[-100:], "summary": self.summary}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add(self, role: str, text: str):
        self.messages.append({"role": role, "text": text, "timestamp": time.time()})
        if len(self.messages) > 100:
            older = self.messages[:-50]
            self._update_summary(older)
            self.messages = self.messages[-50:]
        threading.Thread(target=self._save, daemon=True).start()

    def _update_summary(self, turns: list[dict]):
        key_points = []
        for t in turns:
            txt = t.get("text", "")
            if len(txt) > 10 and not any(w in txt.lower() for w in ("hello", "hi", "ok", "yes", "no")):
                key_points.append(f"{t.get('role')}: {txt[:80]}")
        if key_points:
            self.summary = (self.summary or "") + " " + "; ".join(key_points[-6:])
            self.summary = self.summary.strip()[:600]

    def tokens_used(self) -> int:
        return sum(_estimate_tokens(m.get("text", "")) for m in self.messages)

    def get_context_history(self, max_turns: int = 12) -> str:
        """Format recent conversation turns and summary into a clean context string."""
        history_parts = []
        if self.summary:
            history_parts.append(f"[Earlier Conversation Summary]\n{self.summary}\n")

        recent = self.messages[-max_turns:] if self.messages else []
        for msg in recent:
            role = "User" if msg.get("role") == "user" else "Iris"
            history_parts.append(f"{role}: {msg.get('text', '')}")

        return "\n".join(history_parts)

    def status(self) -> dict:
        used = self.tokens_used()
        max_t = self.max_tokens
        ratio = min(1.0, used / max_t) if max_t else 0.0
        if ratio >= 0.9:
            state, msg = "critical", "Context window filling — rolling summary active."
        elif ratio >= 0.7:
            state, msg = "warning", "Context active with long-term memory."
        else:
            state, msg = "ok", "Context is healthy and persistent."
        return {
            "tokens_used": used,
            "max_tokens": max_t,
            "ratio": round(ratio, 3),
            "status": state,
            "message": msg,
            "message_count": len(self.messages),
            "has_summary": bool(self.summary),
        }

    def new_session(self, keep_summary: bool = True) -> dict:
        cleared = len(self.messages)
        if keep_summary:
            assistant_texts = [m.get("text", "") for m in self.messages if m.get("role") == "assistant"]
            self.summary = (assistant_texts[-1] if assistant_texts else None) or self.summary
        else:
            self.summary = None
        self.messages = []
        self._save()
        return {
            "summary": self.summary,
            "message_count_cleared": cleared,
            "status": "ok",
        }


def create_app(brain=None):
    """Create and configure the FastAPI application.

    Builds the full system stack automatically (unless `brain` is passed):
    core (InferenceEngine + ModelRouter + IrisBrain), memory (3 layers),
    voice (Edge-TTS sweet), vision (screenshot + OCR + file scanner)
    and hands (app launcher, file ops, terminal, web automation).
    """
    app = FastAPI(
        title="IRIS AI Engine API",
        description="REST interface for the IRIS AI engine",
        version="2.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r".*",
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _session = ConversationSession()
    _systems: dict = {}
    _voice_holder: dict = {"engine": None}
    _vision_events: list = []
    _vision_events_lock = threading.Lock()
    _MAX_VISION_EVENTS = 15

    def _log_vision(kind: str, source: str, image_path: Optional[str],
                    description: str, faces: Optional[int] = None, text: Optional[str] = None):
        """Record a vision event so the frontend can show what Iris saw."""
        with _vision_events_lock:
            _vision_events.insert(0, {
                "kind": kind,
                "source": source,
                "image": os.path.basename(image_path) if image_path else None,
                "description": description,
                "faces": faces,
                "text": text,
                "time": time.time(),
            })
            del _vision_events[_MAX_VISION_EVENTS:]

    def _build_stack():
        # Ensure project root "AI model (iris)" is at top of sys.path BEFORE any imports
        _IRIS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if _IRIS_ROOT in sys.path:
            sys.path.remove(_IRIS_ROOT)
        sys.path.insert(0, _IRIS_ROOT)
        if 'core' in sys.modules and not hasattr(sys.modules['core'], 'IrisBrain'):
            del sys.modules['core']

        from core import IrisBrain, IntentDetector, Decider, IrisPersonality, ModelRouter
        from memory import TempLayer, LongTempLayer, DeepLayer, MemoryOrchestrator
        from backend.core.api_keys import APIKeyManager
        from backend.engine.inference_engine import InferenceEngine
        from backend.voice_engine import VoiceEngine
        from vision import ScreenshotCapture, OCREngine, ImageAnalyzer, FileScanner, UIDetector
        from vision import CameraCapture, FaceDetector, PresenceEmotionEngine
        from hands import AppLauncher, MouseKeyboard, FileOps, TerminalExecutor, WebAutomation, TaskExecutor
        from hands import CodeRunner, SystemMonitor, WindowManager, HotkeyListener, SystemControl, UnderstandSystem
        from hands import WhatsAppController, YouTubeController, SocialController

        personality = IrisPersonality({"name": "Iris", "style": "friendly"})
        intent = IntentDetector()
        decider = Decider()
        api_keys = APIKeyManager()
        engine = InferenceEngine(
            config={"backend": "auto", "model_name": "qwen/qwen3.8-27b", "max_tokens": 1536, "timeout": 20},
            api_key_manager=api_keys,
        )
        router = ModelRouter(inference_engine=engine)
        memory = MemoryOrchestrator(TempLayer(), LongTempLayer(), DeepLayer())

        # ── Voice: Edge-TTS female voice (optional) ───────────
        voice_engine = None
        try:
            voice_engine = VoiceEngine(voice="sweet", offline_fallback=True)
            _voice_holder["engine"] = voice_engine
        except Exception as e:
            logger.warning(f"VoiceEngine failed to initialize, continuing without voice: {e}")

        # ── Vision: screen capture (enabled), OCR, file scan ──
        screenshot = ScreenshotCapture(enabled=True)
        ocr = OCREngine()
        image_analyzer = ImageAnalyzer()
        file_scanner = FileScanner()
        ui_detector = UIDetector(ocr_engine=ocr)
        camera = CameraCapture(camera_id=0, enabled=True)
        face_detector = FaceDetector()
        presence_emotion = PresenceEmotionEngine(camera_capture=camera, voice_engine=voice_engine)
        presence_emotion.register_callback(lambda s: personality.set_emotion(s.emotion, s.confidence))

        # ── Hands / automation (safe mode) ─────────────────────
        app_launcher = AppLauncher()
        mouse_keyboard = MouseKeyboard()
        file_ops = FileOps()
        terminal = TerminalExecutor(safe_mode=True)
        web_automation = WebAutomation()
        system_monitor = SystemMonitor()
        window_manager = WindowManager()
        hotkeys = HotkeyListener()
        system_control = SystemControl()
        understand = UnderstandSystem(app_launcher=app_launcher)
        whatsapp = WhatsAppController(window_manager=window_manager, app_launcher=app_launcher)
        social = SocialController(window_manager=window_manager, app_launcher=app_launcher, whatsapp_controller=whatsapp)
        youtube = YouTubeController(window_manager=window_manager, app_launcher=app_launcher, system_control=system_control)

        # CodeRunner: generates content locally (Ollama) with a Groq
        # fallback, writes it to the workspace, and runs it.
        def _groq_generate(prompt: str) -> str:
            try:
                return engine.generate(
                    prompt,
                    system_prompt="You are a coding assistant. Output ONLY the requested file content. "
                                  "No explanations, no markdown fences, no commentary.",
                    max_tokens=4096,
                )
            except Exception as e:
                raise RuntimeError(f"Groq generation failed: {e}")

        code_runner = CodeRunner(generator_fn=_groq_generate, file_ops=file_ops)

        from hands import GameBuilder, WebsiteBuilder
        game_builder = GameBuilder(code_runner=code_runner, file_ops=file_ops, generator_fn=_groq_generate)
        website_builder = WebsiteBuilder(file_ops=file_ops, generator_fn=_groq_generate)

        task_executor = TaskExecutor(
            app_launcher=app_launcher,
            mouse_keyboard=mouse_keyboard,
            file_ops=file_ops,
            terminal=terminal,
            web_automation=web_automation,
            code_runner=code_runner,
            system_monitor=system_monitor,
            window_manager=window_manager,
            hotkeys=hotkeys,
            system_control=system_control,
            understand=understand,
            whatsapp=whatsapp,
            youtube=youtube,
            social=social,
            game_builder=game_builder,
            website_builder=website_builder,
        )

        # Wire ScreenAssistant & Auxiliary Systems to PresenceSentinel
        try:
            from vision.screen_assistant import ScreenAssistant
            screen_assistant = ScreenAssistant()
            presence_emotion.set_auxiliary_systems(
                youtube=youtube,
                screen_assistant=screen_assistant,
                screenshot=screenshot,
                ocr=ocr,
                window_manager=window_manager
            )
        except Exception as se:
            logger.warning(f"Failed to wire ScreenAssistant to presence engine: {se}")

        # Wire TodoManager (Layer 2 memory) and TodoScheduler
        try:
            from core.todo_manager import TodoManager
            from backend.todo_scheduler import TodoScheduler
            long_temp_instance = getattr(memory, "long_temp", None)
            todo_manager = TodoManager(long_temp_layer=long_temp_instance)
            todo_scheduler = TodoScheduler(todo_manager=todo_manager, voice_engine=voice_engine)
            todo_scheduler.start()
        except Exception as te:
            logger.warning(f"Failed to initialize TodoManager/TodoScheduler: {te}")
            todo_manager = None
            todo_scheduler = None

        b = IrisBrain()
        try:
            from core.typo_corrector import TypoCorrector
            b.set_typo_corrector(TypoCorrector(app_launcher=app_launcher))
        except Exception:
            pass
        if todo_manager is not None:
            b.todo_manager = todo_manager
        b.set_intent(intent)
        b.set_decider(decider)
        b.set_personality(personality)
        b.set_model_router(router)
        b.set_memory(memory)
        b.set_voice(voice_engine)
        b.set_vision(screenshot)
        b.set_hands(task_executor)
        b.set_presence(presence_emotion)
        decider.set_hands(task_executor)

        _systems.update({
            "api_keys": api_keys,
            "memory": memory,
            "voice": voice_engine,
            "screenshot": screenshot,
            "ocr": ocr,
            "image_analyzer": image_analyzer,
            "file_scanner": file_scanner,
            "ui_detector": ui_detector,
            "camera": camera,
            "face_detector": face_detector,
            "presence_emotion": presence_emotion,
            "app_launcher": app_launcher,
            "mouse_keyboard": mouse_keyboard,
            "file_ops": file_ops,
            "terminal": terminal,
            "web_automation": web_automation,
            "code_runner": code_runner,
            "task_executor": task_executor,
            "system_monitor": system_monitor,
            "window_manager": window_manager,
            "hotkeys": hotkeys,
            "system_control": system_control,
            "understand": understand,
            "whatsapp": whatsapp,
            "youtube": youtube,
            "todo_manager": todo_manager,
            "todo_scheduler": todo_scheduler,
            "hybrid_router": None,
            "conversation_manager": None,
        })

        try:
            from backend.engine.hybrid_model_router import get_hybrid_router
            from memory.conversation_manager import get_conversation_manager
            from backend.intelligence.music_engine import get_music_lyrics_engine
            _systems["hybrid_router"] = get_hybrid_router(api_key_manager=api_keys)
            _systems["conversation_manager"] = get_conversation_manager()
            _systems["music_engine"] = get_music_lyrics_engine(api_key_manager=api_keys, hybrid_router=_systems["hybrid_router"])
        except Exception as e:
            logger.warning(f"Failed to wire hybrid router / conversation / music manager: {e}")


        # Continuous Voice & Vision Daemons (Hands-free always-on mic & ambient vision)
        try:
            from backend.continuous_voice_daemon import ContinuousVoiceDaemon
            from backend.continuous_vision_daemon import ContinuousVisionDaemon

            def _voice_chat_dispatch(spoken_text: str) -> str:
                req = ChatRequest(message=spoken_text, voice=True, is_voice=True)
                res = chat(req)
                ans = res.response if hasattr(res, "response") else str(res)
                if voice_daemon and ans:
                    voice_daemon.record_assistant_speech(ans)
                return ans

            voice_daemon = ContinuousVoiceDaemon(
                api_key_manager=api_keys,
                voice_engine=voice_engine,
                chat_dispatcher=_voice_chat_dispatch
            )
            vision_daemon = ContinuousVisionDaemon(
                presence_emotion_engine=presence_emotion,
                screenshot_engine=screenshot,
                ocr_engine=ocr,
                window_manager=window_manager
            )
            _systems.update({
                "voice_daemon": voice_daemon,
                "vision_daemon": vision_daemon,
            })
            logger.info("Continuous Voice & Vision Daemons configured.")
        except Exception as v_err:
            logger.warning(f"Continuous Voice/Vision daemons initialization error: {v_err}")

        logger.info("Full stack ready: core + memory + voice + vision + hands + todos + presence + continuous daemons")
        return b, router

    @app.on_event("startup")
    async def startup():
        nonlocal brain
        if brain is None:
            try:
                brain, _router = _build_stack()
                logger.info("IRIS engine stack initialized (all systems)")
            except Exception as e:
                logger.error(f"Engine stack failed to initialize: {e}", exc_info=True)
                brain = None
        if os.environ.get("IRIS_TEST_MODE") == "1":
            logger.info("Test mode active — skipping hardware daemons & slow warmups")
            return

        # Start Always-On Continuous Voice & Vision Daemons
        vd = _systems.get("voice_daemon")
        if vd:
            vd.start()
        vis_d = _systems.get("vision_daemon")
        if vis_d:
            vis_d.start()
        # Fire ALL warm-ups in parallel for fastest startup
        for fn in [_warm_up_llm, _warm_up_voice, _warm_up_camera, _warm_up_mic]:
            threading.Thread(target=fn, daemon=True).start()
        logger.info("IRIS Engine API server started — all warm-ups & continuous daemons launched")

    @app.on_event("shutdown")
    async def shutdown():
        vd = _systems.get("voice_daemon")
        if vd:
            vd.stop()
        vis_d = _systems.get("vision_daemon")
        if vis_d:
            vis_d.stop()

    def _warm_up_llm():
        """Warm up Ollama (offline, primary) then Groq (cloud, fallback) with fast timeouts to avoid startup lag."""
        # 1) Ollama warm-up (offline — quick check, never stalls startup)
        try:
            import urllib.request
            import json as _json
            payload = _json.dumps({
                "model": "llama3.2:3b",
                "prompt": "Say OK",
                "stream": False,
                "options": {"num_predict": 5}
            }).encode()
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=2.0)
            logger.info("Ollama model warmed — offline responses ready")
        except Exception as e:
            logger.info(f"Ollama warmup skipped ({e}), continuing startup...")

        # 1b) Ollama Coding model warm-up (Qwen / GLM)
        for code_model in ["qwen2.5:3b", "glm4:9b"]:
            try:
                payload = _json.dumps({
                    "model": code_model,
                    "prompt": "OK",
                    "stream": False,
                    "options": {"num_predict": 2}
                }).encode()
                req = urllib.request.Request(
                    "http://localhost:11434/api/generate",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req, timeout=2.0)
                logger.info(f"Ollama coding model '{code_model}' warmed up")
                break
            except Exception:
                pass

        # 2) Groq warm-up (cloud fallback)
        try:
            keys = _sys("api_keys")
            if keys:
                key = keys.get_key("groq")
                if key:
                    from openai import OpenAI
                    client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1", timeout=3.0)
                    client.chat.completions.create(
                        model="qwen/qwen3.8-27b",
                        messages=[{"role": "user", "content": "Say OK"}],
                        max_tokens=5,
                    )
                    logger.info("Groq connection warmed — cloud fallback ready")
        except Exception as e:
            logger.warning(f"Groq warmup skipped: {e}")

    def _warm_up_voice():
        """Pre-synthesize top fast replies without blocking or slowing startup."""
        voice = _voice_holder["engine"]
        if voice is None:
            return
        phrases = ["Hey! Ready when you are.", "Anytime 👍"]
        try:
            voice.prewarm(phrases)
        except Exception:
            pass
        logger.info("Voice pre-warm complete")

    def _warm_up_camera():
        """Pre-warm camera and start Presence & Emotion Intelligence daemon upon startup."""
        cam = _systems.get("camera")
        pe = _systems.get("presence_emotion")
        if cam and cam.is_enabled():
            cam.set_keep_alive(True)
            cam.start_stream()
            logger.info("Camera stream started & keep-alive enabled — webcam ready in <1.5s")
        if pe:
            pe.start()
            logger.info("⚔️ Presence & Emotion Intelligence Engine activated at backend startup.")

    def _warm_up_mic():
        """Pre-initialize the microphone so first listen is ~1.5s."""
        try:
            import sounddevice as sd
            # Query devices to trigger driver initialization
            sd.query_devices()
            logger.info("Microphone pre-warmed — audio input ready")
        except Exception as e:
            logger.info(f"Mic warmup skipped: {e}")

    def _guard():
        if brain is None:
            raise HTTPException(status_code=503, detail="AI engine not initialized")

    def _sys(name: str):
        return _systems.get(name)

    # ─── Frontend endpoints ───────────────────────────────

    @app.get("/health")
    async def health():
        return {"status": "ok", "name": "IRIS Engine", "version": "2.0.0"}

    _chat_lock = threading.Lock()

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest):
        _guard()
        with _chat_lock:
            start = time.time()

            # Biometric single-owner security guard:
            pe = _sys("presence_emotion")
            if pe and hasattr(pe, "get_current_state"):
                try:
                    st = pe.get_current_state()
                    req_lower = (request.message or "").lower()
                    is_enroll_cmd = any(w in req_lower for w in (
                        "scan my face", "enroll", "register", "reset", "remove previous",
                        "pevis", "previous", "re-enroll", "re-register", "who am i", "identify",
                        "register newly", "make the list newly", "make a to do list", "im the user",
                        "i am the user", "new list", "clear list"
                    ))
                    is_enrolled = hasattr(pe, "vault") and pe.vault.is_enrolled()
                    sim = getattr(st, "similarity", 0.0)
                    last_verified = getattr(pe, "_last_owner_verified_time", 0.0)
                    is_verified = True  # Local terminal interaction is authorized for Commander
                    if False and is_enrolled and getattr(st, "user_detected", False) and not is_verified and not is_enroll_cmd:
                        logger.warning(f"Rejecting chat interaction: unauthorized individual in front of terminal (sim={sim}).")
                        refusal_text = "Biometric authorization failed. IRIS is configured exclusively for Commander. Commands from unrecognized individuals are prohibited."
                        if request.voice and _voice_holder["engine"]:
                            _voice_holder["engine"].speak(refusal_text, emotion="anger")
                        return ChatResponse(
                            response=refusal_text,
                            intent="security_denied",
                            processing_time=round(time.time() - start, 3),
                        )
                except Exception as pe_err:
                    logger.debug(f"Biometric check in chat error: {pe_err}")

            # Record session active timestamp for time gap memory calculation
            try:
                state_file = os.path.join(os.path.dirname(__file__), "..", "..", "vision", "data", "session_state.json")
                os.makedirs(os.path.dirname(state_file), exist_ok=True)
                with open(state_file, "w", encoding="utf-8") as sf:
                    json.dump({"last_active_timestamp": time.time(), "owner": "Commander"}, sf)
            except Exception:
                pass

            # Resolve Conversation ID (supports person chats & multi-conversation)
            cm = _sys("conversation_manager")
            if cm is None:
                from memory.conversation_manager import get_conversation_manager
                cm = get_conversation_manager()

            conv_id = request.conversation_id
            if request.person_name:
                p_conv = cm.get_or_create_person_chat(request.person_name)
                conv_id = p_conv["id"]
            elif not conv_id:
                active_conv = cm.get_active_or_default_conversation()
                conv_id = active_conv["id"]

            _session.add("user", request.message)
            try:
                cm.add_message(conv_id, role="user", content=request.message)
            except Exception as e:
                logger.debug(f"Could not persist user msg to conversation {conv_id}: {e}")

            # Get model routing status for provider/model tracking
            hr = _sys("hybrid_router")
            if hr is None:
                from backend.engine.hybrid_model_router import get_hybrid_router
                hr = get_hybrid_router(_sys("api_keys"))
            hr_status = hr.get_status() if hr else {}
            provider_used = hr_status.get("active_provider", "groq")
            model_used = hr_status.get("active_model", "qwen/qwen3.8-27b")
            is_offline_used = hr_status.get("is_offline_active", False)

            req_lower = (request.message or "").lower().strip()
            hear_patterns = ["can you hear me", "can you hear my voice", "are you hearing me", "hear my voice", "do you hear me", "can you hear", "are you listening"]
            if any(p in req_lower for p in hear_patterns):
                if request.is_voice:
                    text = "Yes Commander, I can hear your voice clearly! I am listening to you."
                else:
                    text = "Yes, I am listening and I can hear you, Commander."
                intent = "conversation"
            else:
                vision_text = _vision_reply(request.message)
                if vision_text is not None:
                    text = vision_text
                    intent = "vision"
                else:
                    fast = _fast_reply(request.message)
                    confirm_word = request.message.lower().strip() in _CONFIRM_WORDS
                    if fast is not None and not (confirm_word and getattr(brain, "_pending_confirmation", None)):
                        text = fast
                        intent = "greeting"
                    else:
                        recent_msgs = cm.get_messages(conv_id, limit=12) if cm else []
                        context_history_lines = []
                        for m in recent_msgs[:-1]:
                            role_label = "User" if m["role"] == "user" else "Iris"
                            context_history_lines.append(f"{role_label}: {m['content']}")
                        context_history = "\n".join(context_history_lines) if context_history_lines else _session.get_context_history(max_turns=12)
                        result = brain.think(request.message, context={"context_history": context_history, "is_voice": bool(request.is_voice), "conversation_id": conv_id})
                        text = result.get("text", "")
                        intent = result.get("intent")

            _session.add("assistant", text)
            try:
                cm.add_message(conv_id, role="assistant", content=text, provider=provider_used, model=model_used, is_offline=is_offline_used)
            except Exception as e:
                logger.debug(f"Could not persist assistant msg to conversation {conv_id}: {e}")

            if request.voice and _voice_holder["engine"]:
                active_emo = None
                if brain and hasattr(brain, "_personality") and brain._personality:
                    active_emo = getattr(getattr(brain._personality, "state", None), "emotion", None)
                    if active_emo:
                        active_emo = active_emo.lower()
                voice_emo = active_emo or intent
                force_speak = (intent in ("silence_on", "silence_off", "space"))
                _voice_holder["engine"].speak(text, emotion=voice_emo, preset=request.voice_preset, force=force_speak)
            # Record assistant speech in continuous voice daemon to prevent acoustic feedback loop
            vd = _systems.get("voice_daemon")
            if vd and hasattr(vd, "record_assistant_speech") and text:
                vd.record_assistant_speech(text)
            return ChatResponse(
                response=text,
                intent=intent,
                processing_time=round(time.time() - start, 3),
                provider=provider_used,
                model=model_used,
                is_offline=is_offline_used,
                conversation_id=conv_id,
            )

    @app.get("/conversation/history")
    async def conversation_history():
        return {
            "messages": _session.messages,
            "summary": _session.summary,
            "count": len(_session.messages),
        }

    @app.post("/conversation/new-session")
    async def conversation_new_session():
        return _session.new_session(keep_summary=True)

    # ─── Hybrid Routing & Model Selection Endpoints ───────────

    @app.get("/model/status")
    async def get_model_status():
        hr = _sys("hybrid_router")
        if hr is None:
            from backend.engine.hybrid_model_router import get_hybrid_router
            hr = get_hybrid_router(_sys("api_keys"))
        return hr.get_status()

    @app.post("/model/select")
    async def select_model(data: dict):
        hr = _sys("hybrid_router")
        if hr is None:
            from backend.engine.hybrid_model_router import get_hybrid_router
            hr = get_hybrid_router(_sys("api_keys"))
        mode = data.get("mode", "auto")
        provider = data.get("provider")
        model = data.get("model")
        hr.set_selection(mode=mode, provider=provider, model=model)
        return hr.get_status()

    @app.get("/model/ollama/models")
    async def get_ollama_models():
        from backend.engine.ollama_client import get_ollama_client
        oc = get_ollama_client()
        return {"models": oc.list_models(), "available": oc.is_available()}

    # ─── Multi-Conversation & Person Chat Endpoints ───────────

    @app.get("/conversations")
    async def list_conversations(search: Optional[str] = None, person: Optional[str] = None):
        cm = _sys("conversation_manager")
        if cm is None:
            from memory.conversation_manager import get_conversation_manager
            cm = get_conversation_manager()
        return {"conversations": cm.list_conversations(search=search, person_name=person)}

    @app.post("/conversations")
    async def create_conversation(data: dict):
        cm = _sys("conversation_manager")
        if cm is None:
            from memory.conversation_manager import get_conversation_manager
            cm = get_conversation_manager()
        title = data.get("title", "New Chat")
        person = data.get("person_name")
        sys_prompt = data.get("system_prompt")
        if person:
            conv = cm.get_or_create_person_chat(person)
        else:
            conv = cm.create_conversation(title=title, person_name=person, system_prompt=sys_prompt)
        return conv

    @app.get("/conversations/{conv_id}")
    async def get_conversation_details(conv_id: str, limit: int = 50):
        cm = _sys("conversation_manager")
        if cm is None:
            from memory.conversation_manager import get_conversation_manager
            cm = get_conversation_manager()
        conv = cm.get_conversation(conv_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        messages = cm.get_messages(conv_id, limit=limit)
        return {"conversation": conv, "messages": messages}

    @app.put("/conversations/{conv_id}")
    async def rename_conversation_endpoint(conv_id: str, data: dict):
        cm = _sys("conversation_manager")
        if cm is None:
            from memory.conversation_manager import get_conversation_manager
            cm = get_conversation_manager()
        new_title = data.get("title", "")
        ok = cm.rename_conversation(conv_id, new_title)
        return {"success": ok, "id": conv_id, "title": new_title}

    @app.delete("/conversations/{conv_id}")
    async def delete_conversation_endpoint(conv_id: str):
        cm = _sys("conversation_manager")
        if cm is None:
            from memory.conversation_manager import get_conversation_manager
            cm = get_conversation_manager()
        ok = cm.delete_conversation(conv_id)
        return {"success": ok, "id": conv_id}

    @app.post("/conversations/person/{person_name}")
    async def open_person_chat(person_name: str):
        cm = _sys("conversation_manager")
        if cm is None:
            from memory.conversation_manager import get_conversation_manager
            cm = get_conversation_manager()
        conv = cm.get_or_create_person_chat(person_name)
        messages = cm.get_messages(conv["id"], limit=50)
        return {"conversation": conv, "messages": messages}

    # ─── Music, Singing & Lyrics Recognition Endpoints ────────
    @app.get("/music/last-song")
    async def get_last_identified_song():
        from backend.intelligence.music_engine import get_music_lyrics_engine
        me = _sys("music_engine") or get_music_lyrics_engine()
        song = me.get_last_song()
        return {"song": song}

    @app.post("/music/identify")
    async def identify_music_lyrics(data: dict):
        text = data.get("text", "")
        from backend.intelligence.music_engine import get_music_lyrics_engine
        me = _sys("music_engine") or get_music_lyrics_engine()
        result = me.analyze_input(text)
        return {"result": result}


    @app.get("/status")
    async def status():
        if brain is None:
            return {"status": "engine_offline"}
        voice = _voice_holder["engine"]
        return {
            "status": "ok",
            "name": brain.name,
            "mode": brain.get_mode(),
            "awake": brain.is_awake,
            "processing": brain.processing,
            "voice_available": voice is not None,
            "speaking": voice.is_speaking() if voice else False,
            "vision_available": brain._vision is not None,
            "hands_available": brain._hands is not None,
            "memory_available": brain._memory is not None,
            "conversation": _session.status(),
        }

    @app.post("/voice/stop")
    def voice_stop():
        voice = _voice_holder.get("engine")
        if voice and hasattr(voice, "stop"):
            voice.stop()
        return {"status": "ok", "speaking": False}

    @app.get("/system")
    async def system():
        if brain is None:
            return {"status": "engine_offline"}
        return {
            "name": brain.name,
            "mode": brain.get_mode(),
            "awake": brain.is_awake,
            "processing": brain.processing,
            "thoughts_logged": len(brain.thought_log),
            "memory_available": brain._memory is not None,
            "voice_available": brain._voice is not None,
            "vision_available": brain._vision is not None,
            "hands_available": brain._hands is not None,
            "model_router": brain._model_router is not None,
        }

    @app.get("/conversation/status")
    async def conversation_status():
        return _session.status()

    # Note: /conversation/new-session is defined above (line ~698).
    # Removed duplicate route that previously shadowed it.

    @app.get("/conversation/summary")
    async def conversation_summary():
        return {"summary": _session.summary}

    @app.post("/conversation/max-tokens")
    async def conversation_max_tokens(request: MaxTokensRequest):
        if request.max_tokens < 100 or request.max_tokens > 4000:
            raise HTTPException(status_code=400, detail="max_tokens must be between 100 and 4000")
        _session.max_tokens = request.max_tokens
        return {"max_tokens": _session.max_tokens, "status": "ok"}

    # ─── Memory system ────────────────────────────────────

    @app.get("/memory")
    async def memory():
        if brain is None or brain._memory is None:
            return {"memories": [], "available": False}
        try:
            stats = brain._memory.get_stats() if hasattr(brain._memory, "get_stats") else {}
            return {"memories": [], "available": True, "stats": stats}
        except Exception:
            return {"memories": [], "available": True}

    @app.get("/memory/stats")
    async def memory_stats():
        mem = _sys("memory")
        if mem is None:
            raise HTTPException(status_code=503, detail="Memory not available")
        stats = mem.get_stats() if hasattr(mem, "get_stats") else {}
        return {"available": True, "stats": stats}

    @app.post("/memory/store")
    async def memory_store(request: MemoryStoreRequest):
        mem = _sys("memory")
        if mem is None:
            raise HTTPException(status_code=503, detail="Memory not available")
        mem.store(request.key, request.value, permanent=True)
        return {"success": True, "key": request.key}

    @app.get("/memory/recall/{key}")
    async def memory_recall(key: str):
        mem = _sys("memory")
        if mem is None:
            raise HTTPException(status_code=503, detail="Memory not available")
        value = mem.get(key)
        if value is None:
            raise HTTPException(status_code=404, detail="Memory not found")
        content = value.get("content", value) if isinstance(value, dict) else value
        return {"key": key, "value": content}

    # ─── Voice system ─────────────────────────────────────

    @app.post("/voice/say")
    def voice_say(request: VoiceSayRequest):
        voice = _voice_holder["engine"]
        if voice is None:
            raise HTTPException(status_code=503, detail="Voice not available in headless API mode")
        voice.speak(request.text, preset=request.preset)
        return {"success": True, "text": request.text}

    @app.get("/voice/info")
    async def voice_info():
        voice = _voice_holder["engine"]
        if voice is None:
            raise HTTPException(status_code=503, detail="Voice not available in headless API mode")
        return voice.get_status()

    @app.get("/voice/clones")
    async def voice_clones():
        voice = _voice_holder["engine"]
        if voice is None:
            raise HTTPException(status_code=503, detail="Voice not available in headless API mode")
        return voice.list_clones()

    @app.post("/voice/set_preset")
    async def voice_set_preset(data: dict):
        preset = data.get("preset", "hindi_sweet")
        voice = _voice_holder["engine"]
        if voice is None:
            raise HTTPException(status_code=503, detail="Voice not available in headless API mode")
        ok = voice.set_voice(preset)
        return {"success": ok, "preset": preset, "status": voice.get_status()}

    @app.post("/voice/speak")
    async def voice_speak(data: dict):
        text = data.get("text", "")
        emotion = data.get("emotion", "neutral")
        voice = _voice_holder["engine"]
        if voice is None:
            raise HTTPException(status_code=503, detail="Voice not available in headless API mode")
        if text:
            voice.speak(text, emotion=emotion)
        return {"success": True, "text": text, "status": voice.get_status()}

    @app.post("/voice/silent")
    async def voice_silent(data: dict):
        enabled = data.get("enabled", True)
        voice = _voice_holder["engine"]
        pe = _sys("presence_emotion")
        if voice and hasattr(voice, "set_silent_mode"):
            voice.set_silent_mode(enabled)
        if pe and hasattr(pe, "set_silent_mode"):
            pe.set_silent_mode(enabled)
        return {"success": True, "silent_mode": enabled, "status": voice.get_status() if voice else {}}

    @app.get("/voice/silent")
    async def get_voice_silent():
        voice = _voice_holder["engine"]
        is_silent = voice.is_silent_mode() if voice and hasattr(voice, "is_silent_mode") else False
        return {"silent_mode": is_silent}

    @app.post("/voice/stop")
    @app.post("/api/voice/stop")
    async def voice_stop():
        voice = _voice_holder["engine"]
        if voice and hasattr(voice, "stop"):
            voice.stop()
        return {"status": "ok", "speaking": False}


    # ─── Vision system ────────────────────────────────────

    GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-flash"]
    GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def _describe_image(image_path: str, prompt: str = "Describe what you see in this image in 1-2 short sentences.") -> str:
        """Send an image to Gemini Flash (fallback: OpenRouter, Ollama, local analysis) and return a description."""
        import urllib.request
        import urllib.error
        keys = _sys("api_keys")
        gemini_key = keys.get_key("google") if keys else None
        openrouter_key = keys.get_key("openrouter") if keys else None
        try:
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
        except Exception as e:
            return f"I captured the frame, but failed to read the image: {e}"

        if gemini_key:
            gemini_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-pro"]
            for model in gemini_models:
                try:
                    mime = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                    body = {
                        "contents": [{
                            "parts": [
                                {"text": prompt},
                                {"inline_data": {"mime_type": mime, "data": b64}},
                            ]
                        }],
                        "generationConfig": {"maxOutputTokens": 200, "temperature": 0.4},
                    }
                    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                                 headers={"Content-Type": "application/json"}, method="POST")
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        result = json.loads(resp.read().decode())
                    try:
                        text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                        if text:
                            return text
                    except (KeyError, IndexError):
                        logger.warning(f"Gemini {model} parse failed: {str(result)[:200]}")
                except Exception as e:
                    logger.warning(f"Gemini {model} failed: {e}")
                    continue

        if openrouter_key:
            try:
                body = {
                    "model": "qwen/qwen2.5-vl-72b-instruct",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        ],
                    }],
                    "max_tokens": 200,
                }
                req = urllib.request.Request(
                    "https://openrouter.ai/api/v1/chat/completions",
                    data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {openrouter_key}"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    result = json.loads(resp.read().decode())
                return result["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.warning(f"OpenRouter vision failed: {e}")

        # Local Ollama Multimodal Vision Fallback
        try:
            url = "http://127.0.0.1:11434/api/generate"
            body = {"model": "llama3.2-vision", "prompt": prompt, "images": [b64], "stream": False}
            req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode())
                txt = res.get("response", "").strip()
                if txt:
                    return txt
        except Exception:
            pass

        local_desc = _describe_local(image_path)
        if local_desc:
            return f"Visual capture complete: {local_desc}"

        return "I captured your screen, but vision services are currently unavailable."

    # ── Chat vision interception ──────────────────────────
    # Vision requests are handled here (before the text-only LLM), so Iris
    # actually looks through the camera / screen instead of saying
    # "I'm a text-based AI model".

    _VISION_KEYS = {
        "ocr": [
            "read the screen", "read the text", "read the text on the screen", "read what's on my screen",
            "read my screen", "what does it say", "what does the screen say", "what is written",
            "transcribe the screen", "read this",
        ],
        "faces": [
            "detect faces", "how many faces", "face detection", "look for faces",
            "who is with me", "is anyone there", "who is there with me", "see who is there",
        ],
        "camera": [
            "look at me", "look at my face", "look at the camera", "look at your camera",
            "see me", "use your camera", "open your camera", "take a picture", "take a photo",
            "capture me", "look through the camera", "look at me through the camera",
            "what are you seeing on the webcam", "what are you seeing on webcam",
            "what do you see on the webcam", "what do you see on webcam",
            "what are you looking at", "what can you see through the camera",
            "show me what you see", "can you see me", "are you looking at me",
            "do you see me", "can you see anything",
        ],
        "screen": [
            "look at my screen", "look at the screen", "look at my desktop", "look at my display",
            "see the screen", "see my screen", "what do you see", "what do you see on my screen",
            "what is on my screen", "what's on my screen", "take a screenshot", "screenshot",
            "screen capture", "capture the screen", "look at my computer",
            "what can you see right now", "what do you see right now", "can you see my screen",
            "what are you seeing right now",
        ],
        "ui": [
            "detect ui", "ui elements", "find buttons", "identify ui", "see the interface",
            "look at the interface", "find the buttons", "what is on the interface",
        ],
    }

    # Keyword fallback for natural phrasings ("... on the webcam", "... through the camera")
    _VISION_KEYWORDS = {
        "ocr": ["ocr", "transcribe"],
        "faces": ["how many faces", "detect faces", "face detection"],
        "camera": ["webcam", "through the camera", "on camera", "camera feed", "your camera"],
        "screen": ["screenshot", "screen capture", "capture the screen"],
        "ui": ["interface", "ui elements"],
    }

    def _vision_intent(message: str) -> Optional[str]:
        m = message.lower().strip()
        # Fast exclusions: actions to open, create, navigate, minimize, or manipulate windows/folders
        if re.search(r"\b(?:go\s+to|open|create|make|delete|minimize|maximize|snap|close|launch|run|save|find|list|show\s+desktop)\b", m):
            return None
        for intent in ("ocr", "faces", "camera", "screen", "ui"):
            for phrase in _VISION_KEYS[intent]:
                if phrase in m:
                    return intent
        for intent in ("ocr", "faces", "camera", "screen", "ui"):
            for kw in _VISION_KEYWORDS[intent]:
                if kw in m:
                    return intent
        if re.search(r"\b(what do you see|what can you see|what are you seeing|can you see|do you see)\b", m):
            return "screen"
        return None

    def _describe_local(image_path: str) -> Optional[str]:
        """Tiny offline fallback description when no vision API key exists."""
        try:
            import cv2
            img = cv2.imread(image_path)
            if img is None:
                return None
            h, w = img.shape[:2]
            b, g, r = (float(img[..., i].mean()) for i in range(3))
            brightness = round((0.114 * b + 0.587 * g + 0.299 * r) / 255, 2)
            mx = max(r, g, b)
            if mx < 60:
                tone = "a very dark image"
            elif r > g + 40 and r > b + 40:
                tone = "a reddish image"
            elif g > r + 40 and g > b + 40:
                tone = "a greenish image"
            elif b > r + 40 and b > g + 40:
                tone = "a bluish image"
            elif mx > 200 and abs(r - g) < 30 and abs(g - b) < 30:
                tone = "a very bright, mostly white image"
            else:
                tone = "a neutral, colorful image"
            return f"a {w}x{h} frame with average brightness {brightness:.2f} and {tone}"
        except Exception:
            return None

    def _vision_reply(message: str) -> Optional[str]:
        """Handle vision requests in chat. Returns a reply string, or None if the
        message is not a vision request (falls through to the LLM)."""
        intent = _vision_intent(message)
        if intent is None:
            return None
        ss = _sys("screenshot")
        cam = _sys("camera")
        ocr_engine = _sys("ocr")
        face = _sys("face_detector")
        ui = _sys("ui_detector")
        try:
            if intent == "camera":
                if cam is None or not cam.is_enabled():
                    return "My camera module isn't enabled right now."
                path = cam.capture()
                if not path:
                    err = (cam.get_status() or {}).get("last_error") or "unknown error"
                    return (f"I couldn't access the camera ({err}). Please check that the "
                            "camera isn't in use by another app and that Windows privacy "
                            "settings allow camera access.")
                quality = _frame_quality(path)
                if quality != "ok":
                    reason = ("the view is too dark or the lens is covered" if quality == "blank"
                              else "the view is too blurry to make out")
                    reply = f"I looked through your camera, but I can't see anything clearly — {reason}. Please make sure the camera has a clear, well-lit view."
                    _log_vision("camera", "camera", path, reply)
                    return reply
                desc = _describe_image(path, "Describe what you see in this photo in 1-2 short sentences. If a person is visible, describe their appearance, hair, clothing and expression. If the image is too dark, blurry, or contains no visible subject, reply with exactly: " + _NO_CONTENT_MARKER)
                if _NO_CONTENT_MARKER in desc:
                    reply = ("I looked through your camera, but I can't make out anything "
                             "clearly — the view seems dark or blurry.")
                    _log_vision("camera", "camera", path, reply)
                    return reply
                if "aren't responding" in desc or not desc.strip():
                    reply = ("I can see through the camera, but I'm having trouble understanding what I'm seeing. "
                             "This usually happens if my vision API keys aren't set up correctly. "
                             "Please check your Google or OpenRouter API keys.")
                    _log_vision("camera", "camera", path, reply)
                    return reply
                face_count = face.count(path) if face and face.is_available() else 0
                extra = f" I can also see {face_count} face{'s' if face_count != 1 else ''}." if face_count else ""
                reply = f"I'm looking through your camera now. {desc}{extra}"
                _log_vision("camera", "camera", path, reply, faces=face_count or None)
                return reply

            if intent == "screen":
                vis_d = _sys("vision_daemon")
                if vis_d:
                    ctx = vis_d.get_latest_context()
                    if ctx.get("screen_summary") and (time.time() - ctx.get("last_screen_scan", 0) < 25):
                        win = ctx.get("active_window") or "your desktop"
                        act = ctx.get("activity_type") or "General Work"
                        summ = ctx.get("screen_summary")
                        reply = f"I am continuously observing your screen. You are active in {win} ({act}). {summ}"
                        _log_vision("screen", "screen", None, reply)
                        return reply

                if ss is None or not ss.is_enabled():
                    return "My screen capture module isn't enabled right now."
                path = ss.capture()
                if not path:
                    return "I tried to capture the screen but it failed. Please try again."
                if _frame_quality(path) != "ok":
                    reply = "I looked at your screen, but it appears to be off, black, or blurry — there's nothing I can read from it."
                    _log_vision("screen", "screen", path, reply)
                    return reply
                desc = _describe_image(path, "Describe what is visible on this computer screen in 1-2 short sentences. Mention the application or window if you can tell. If the screen is black, blank, or shows no visible content, reply with exactly: " + _NO_CONTENT_MARKER)
                if _NO_CONTENT_MARKER in desc:
                    reply = "I looked at your screen, but it appears to be off or showing a black screen."
                    _log_vision("screen", "screen", path, reply)
                    return reply
                if "aren't responding" in desc or not desc.strip():
                    reply = ("I can see your screen, but I'm having trouble understanding what's on it. "
                             "This usually happens if my vision API keys aren't set up correctly. "
                             "Please check your Google or OpenRouter API keys.")
                    _log_vision("screen", "screen", path, reply)
                    return reply
                reply = f"I looked at your screen. {desc}"
                _log_vision("screen", "screen", path, reply)
                return reply

            if intent == "ocr":
                if ss is None or not ss.is_enabled():
                    return "My screen capture module isn't enabled right now."
                path = ss.capture()
                if not path:
                    return "I tried to capture the screen but it failed. Please try again."
                if ocr_engine and ocr_engine.is_available():
                    text = ocr_engine.extract_text(path)
                    if text and text.strip():
                        return f'I read this on your screen: "{text.strip()}"'
                desc = _describe_image(path, "Transcribe ALL text visible in this image exactly as written. If there is no readable text, reply with exactly: No text found.")
                if "No text found" in desc:
                    reply = "I looked at your screen but couldn't find any readable text."
                    _log_vision("ocr", "screen", path, reply)
                    return reply
                if "aren't responding" in desc:
                    reply = ("I can see your screen but I can't read the text right now — the "
                             "offline OCR engine (easyocr) isn't installed and no vision API "
                             "key is configured. Install easyocr or add a Google Gemini key.")
                    _log_vision("ocr", "screen", path, reply)
                    return reply
                reply = f"I read this on your screen: {desc}"
                _log_vision("ocr", "screen", path, reply, text=desc)
                return reply

            if intent == "faces":
                path = cam.capture() if cam and cam.is_enabled() else (ss.capture() if ss and ss.is_enabled() else None)
                if not path:
                    return "I couldn't capture an image to look for faces."
                if not face or not face.is_available():
                    return "My face detection module isn't available right now."
                count = face.count(path)
                if count == 0:
                    reply = "I looked, but I don't see any faces right now."
                    _log_vision("faces", "camera" if path and "camera" in os.path.basename(path) else "screen", path, reply)
                    return reply
                reply = f"I see {count} face{'s' if count != 1 else ''} in front of me."
                _log_vision("faces", "camera" if path and "camera" in os.path.basename(path) else "screen", path, reply, faces=count)
                return reply

            if intent == "ui":
                if ss is None or not ss.is_enabled():
                    return "My screen capture module isn't enabled right now."
                path = ss.capture()
                if not path or ui is None:
                    return "I couldn't analyze the interface right now."
                elements = ui.detect_elements(path)
                buttons = [e for e in elements if e.get("type") == "button"]
                fields = [e for e in elements if e.get("type") == "input_field"]
                windows = [e for e in elements if e.get("type") == "window"]
                parts = []
                if buttons:
                    parts.append(f"{len(buttons)} button(s): " + ", ".join(e.get("text", "") for e in buttons[:5]))
                if fields:
                    parts.append(f"{len(fields)} input field(s): " + ", ".join(e.get("text", "") for e in fields[:5]))
                if windows:
                    parts.append("open window(s): " + ", ".join(e.get("title", e.get("name", "")) for e in windows[:5]))
                if not parts:
                    reply = "I looked at your screen but couldn't identify clear UI elements."
                    _log_vision("ui", "screen", path, reply)
                    return reply
                reply = "I scanned your interface and found " + "; ".join(parts) + "."
                _log_vision("ui", "screen", path, reply)
                return reply

        except Exception as e:
            logger.error(f"Vision chat handler failed: {e}", exc_info=True)
            return "I tried to use my vision but something went wrong. Please try again."
        return None

    @app.get("/vision/status")
    async def vision_status():
        ss = _sys("screenshot")
        ocr = _sys("ocr")
        cam = _sys("camera")
        face = _sys("face_detector")
        keys = _sys("api_keys")
        return {
            "available": ss is not None,
            "screenshot_enabled": ss.is_enabled() if ss else False,
            "camera": cam.get_status() if cam else {"enabled": False},
            "face_detection": face.get_status() if face else {"available": False},
            "ocr": ocr.get_status() if ocr else {"available": False},
            "presence_emotion_available": _sys("presence_emotion") is not None,
            "vision_api_keys": bool(keys and (keys.get_key("google") or keys.get_key("openrouter"))),
        }

    @app.get("/vision/presence-emotion")
    async def vision_presence_emotion():
        pe = _sys("presence_emotion")
        if pe is None:
            return {"user_detected": False, "emotion": "neutral", "status": "offline"}
        return pe.get_current_state().to_dict()

    @app.get("/presence/status")
    async def presence_status():
        pe = _sys("presence_emotion")
        if pe is None:
            return {"status": "none", "user_detected": False, "is_owner": False, "emotion": "neutral", "speaking": False}
        st = pe.get_current_state()
        bio = pe.get_biometric_info() if hasattr(pe, "get_biometric_info") else {}
        state_label = "owner" if (st.user_detected and st.is_owner) else ("stranger" if st.user_detected else "none")
        return {
            "status": state_label,
            "user_detected": st.user_detected,
            "is_owner": st.is_owner,
            "user_name": st.user_name,
            "similarity": st.similarity,
            "emotion": st.emotion,
            "confidence": st.confidence,
            "speaking": st.speaking,
            "arousal": st.arousal,
            "valence": st.valence,
            "enabled": pe.is_enabled(),
            "biometric_format": "face_parameters_only",
            "raw_photo_stored": False,
            "biometric_profile": bio,
        }

    @app.get("/emotion/current")
    async def emotion_current():
        pe = _sys("presence_emotion")
        if pe is None:
            return {"emotion": "neutral", "confidence": 0.0, "speaking": False}
        st = pe.get_current_state()
        return {
            "emotion": st.emotion,
            "confidence": st.confidence,
            "valence": st.valence,
            "arousal": st.arousal,
            "speaking": st.speaking,
            "acoustic_energy": st.acoustic_energy,
        }

    @app.post("/presence/enroll")
    async def presence_enroll(request: Optional[PresenceEnrollRequest] = None):
        pe = _sys("presence_emotion")
        if pe is None:
            raise HTTPException(status_code=503, detail="Presence engine unavailable")
        name = (request.name if request else "Commander") or "Commander"
        result = pe.enroll_current_face(name=name)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Enrollment failed"))
        return result

    @app.post("/presence/toggle")
    async def presence_toggle(request: Optional[PresenceToggleRequest] = None):
        pe = _sys("presence_emotion")
        if pe is None:
            raise HTTPException(status_code=503, detail="Presence engine unavailable")
        enable = request.enable if request else None
        new_state = pe.toggle(enable=enable)
        return {"enabled": new_state, "status": "ok"}

    @app.get("/proactive/events")
    async def proactive_events(since_id: Optional[str] = None):
        pe = _sys("presence_emotion")
        if pe is None:
            return {"events": [], "current_state": {"user_detected": False, "emotion": "neutral"}}
        events = pe.get_proactive_events(since_id=since_id)
        current = pe.get_current_state().to_dict()
        return {"events": events, "current_state": current}

    @app.post("/emotion/simulate")
    async def emotion_simulate(request: SimulateEmotionRequest):
        pe = _sys("presence_emotion")
        if pe is None:
            raise HTTPException(status_code=503, detail="Presence emotion engine unavailable")
        evt = pe.trigger_manual_emotion(request.emotion)
        return {"status": "ok", "simulated": request.emotion, "event": evt}

    @app.post("/presence/reset")
    @app.post("/api/presence/reset")
    async def presence_reset():
        pe = _sys("presence_emotion")
        if pe is None:
            raise HTTPException(status_code=503, detail="Presence engine unavailable")
        pe.reset_biometrics()
        return {"status": "ok", "message": "Biometric profile wiped. Look at camera to register newly."}

    @app.post("/presence/re-enroll")
    @app.post("/api/presence/re-enroll")
    async def presence_re_enroll(request: Optional[PresenceEnrollRequest] = None):
        pe = _sys("presence_emotion")
        if pe is None:
            raise HTTPException(status_code=503, detail="Presence engine unavailable")
        name = (request.name if request else "Commander") or "Commander"
        result = pe.reset_and_re_enroll(name=name)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Re-enrollment failed"))
        return result

    # ─── To-Do Endpoints (2nd Layer Memory: LongTempLayer) ───────────────
    class TodoCreateRequest(BaseModel):
        task: str
        due_time: Optional[float] = None
        remind_in_seconds: Optional[float] = None

    class TodoUpdateRequest(BaseModel):
        completed: Optional[bool] = None

    @app.get("/todos")
    @app.get("/api/todos")
    async def get_todos():
        tm = _sys("todo_manager")
        if tm is None:
            return {"todos": []}
        return {"todos": tm.get_all_todos()}

    @app.post("/todos")
    @app.post("/api/todos")
    async def create_todo(req: TodoCreateRequest):
        tm = _sys("todo_manager")
        if tm is None:
            raise HTTPException(status_code=503, detail="TodoManager not available")
        todo = tm.add_todo(task=req.task, due_time=req.due_time, remind_in_seconds=req.remind_in_seconds)
        return {"status": "ok", "todo": todo}

    @app.patch("/todos/{todo_id}")
    @app.patch("/api/todos/{todo_id}")
    async def toggle_todo(todo_id: str, req: Optional[TodoUpdateRequest] = None):
        tm = _sys("todo_manager")
        if tm is None:
            raise HTTPException(status_code=503, detail="TodoManager not available")
        completed = req.completed if req else None
        res = tm.toggle_todo(todo_id, completed=completed)
        return {"status": "ok", "todo": res}

    @app.delete("/todos/{todo_id}")
    @app.delete("/api/todos/{todo_id}")
    async def delete_todo(todo_id: str):
        tm = _sys("todo_manager")
        if tm is None:
            raise HTTPException(status_code=503, detail="TodoManager not available")
        ok = tm.delete_todo(todo_id)
        return {"status": "ok", "deleted": ok}

    @app.post("/todos/clear")
    @app.post("/api/todos/clear")
    async def todos_clear():
        tm = _sys("todo_manager")
        if tm is None:
            raise HTTPException(status_code=503, detail="TodoManager not available")
        count = tm.clear_all_todos()
        return {"status": "ok", "cleared": count}

    @app.get("/presence/hud-state")
    @app.get("/api/presence/hud-state")
    async def presence_hud_state():
        pe = _sys("presence_emotion")
        if pe is None:
            return {"user_detected": False, "emotion": "neutral", "is_owner": False, "is_lips_moving": False, "is_away": False, "away_duration": 0.0}
        return pe.get_current_state().to_dict()

    @app.post("/vision/see")
    async def vision_see():
        _guard()
        ss = _sys("screenshot")
        if ss is None or not ss.is_enabled():
            raise HTTPException(status_code=503, detail="Vision not available")
        path = ss.capture()
        if not path:
            raise HTTPException(status_code=503, detail="Screenshot capture failed")
        if _frame_quality(path) != "ok":
            description = "The screen appears to be off, black, or blurry — there's nothing visible."
        else:
            description = _describe_image(path, "Describe what you see in this image in 1-2 short sentences. If the image is too dark, blurry, or contains no visible subject, reply with exactly: " + _NO_CONTENT_MARKER)
            if _NO_CONTENT_MARKER in description:
                description = "The screen appears to be off, black, or blurry — there's nothing visible."
            elif "aren't responding" in description:
                local = _describe_local(path)
                description = f"I can see {local}." if local else description
        _log_vision("screen", "screen", path, description)
        return {"screenshot": os.path.abspath(path), "description": description}

    @app.post("/vision/camera")
    async def vision_camera():
        _guard()
        cam = _sys("camera")
        if cam is None or not cam.is_enabled():
            raise HTTPException(status_code=503, detail="Camera not available")
        path = cam.capture()
        if not path:
            err = (cam.get_status() or {}).get("last_error") or "unknown error"
            raise HTTPException(status_code=503, detail=f"Camera capture failed: {err}")
        if _frame_quality(path) != "ok":
            description = "I can't see anything clearly — the view is too dark or the lens is blocked."
        else:
            description = _describe_image(path, "Describe what you see in this photo in 1-2 short sentences. If the image is too dark, blurry, or contains no visible subject, reply with exactly: " + _NO_CONTENT_MARKER)
            if _NO_CONTENT_MARKER in description:
                description = "I can't see anything clearly — the view is too dark or the lens is blocked."
            elif "aren't responding" in description:
                local = _describe_local(path)
                description = f"I can see {local}." if local else description
        _log_vision("camera", "camera", path, description)
        return {"photo": os.path.abspath(path), "description": description}

    @app.get("/vision/last")
    async def vision_last():
        with _vision_events_lock:
            events = [
                {**e, "time_ago": round(time.time() - e["time"], 1),
                 "url": f"/api/vision/image/{e['image']}" if e.get("image") else None}
                for e in _vision_events
            ]
        return {"events": events}

    @app.get("/vision/image/{filename}")
    async def vision_image(filename: str):
        safe = os.path.basename(filename)
        if safe != filename or not safe.lower().endswith((".png", ".jpg", ".jpeg")):
            raise HTTPException(status_code=400, detail="Invalid image name")
        camera_dir = os.path.join(os.environ.get("TEMP", "."), "iris_vision")
        for d in (camera_dir, os.getcwd()):
            p = os.path.join(d, safe)
            if os.path.isfile(p):
                return FileResponse(p)
        raise HTTPException(status_code=404, detail="Image not found")

    @app.get("/vision/preview")
    async def vision_preview():
        """Live MJPEG stream of the webcam — shows in the browser exactly
        what Iris sees through her camera."""
        cam = _sys("camera")
        pe = _sys("presence_emotion")
        if cam is None or not cam.is_enabled():
            raise HTTPException(status_code=503, detail="Camera not available")
        cam.start_stream()

        def gen():
            import cv2
            try:
                while True:
                    frame = cam.get_latest_frame()
                    if frame is None:
                        time.sleep(0.1)
                        continue
                    if pe is not None:
                        st = pe.get_current_state()
                        frame = pe.annotate_frame(frame, st)
                    h, w = frame.shape[:2]
                    if w > 800:
                        scale = 800.0 / w
                        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
                    ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    if not ok:
                        time.sleep(0.05)
                        continue
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                           + jpg.tobytes() + b"\r\n")
                    time.sleep(0.08)
            except GeneratorExit:
                pass
            finally:
                cam.stop_stream()

        return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")

    @app.get("/camera/devices")
    async def camera_devices():
        cam = _sys("camera")
        if cam is None:
            return {"active_camera": 0, "available_cameras": [0]}
        devices = cam.get_available_cameras()
        return {"active_camera": cam._camera_id, "available_cameras": devices}

    @app.post("/camera/switch")
    async def camera_switch(camera_id: int):
        cam = _sys("camera")
        if cam is None:
            raise HTTPException(status_code=503, detail="Camera system unavailable")
        cam.switch_camera(camera_id)
        return {"status": "ok", "active_camera": cam._camera_id}

    @app.post("/vision/faces")
    async def vision_faces():
        _guard()
        cam = _sys("camera")
        ss = _sys("screenshot")
        face = _sys("face_detector")
        if face is None or not face.is_available():
            raise HTTPException(status_code=503, detail="Face detection not available")
        path = cam.capture() if cam and cam.is_enabled() else (ss.capture() if ss and ss.is_enabled() else None)
        if not path:
            raise HTTPException(status_code=503, detail="Could not capture an image for face detection")
        faces = face.detect(path)
        return {"count": len(faces), "faces": faces, "source": os.path.abspath(path)}

    @app.post("/vision/ui")
    async def vision_ui():
        _guard()
        ss = _sys("screenshot")
        ui = _sys("ui_detector")
        if ss is None or not ss.is_enabled() or ui is None:
            raise HTTPException(status_code=503, detail="UI detection not available")
        path = ss.capture()
        if not path:
            raise HTTPException(status_code=503, detail="Screenshot capture failed")
        elements = ui.detect_elements(path)
        return {"count": len(elements), "elements": elements, "screenshot": os.path.abspath(path)}

    @app.post("/vision/scan")
    async def vision_scan(request: VisionScanRequest):
        fs = _sys("file_scanner")
        if fs is None:
            raise HTTPException(status_code=503, detail="File scanner not available")
        folder = request.folder or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        if not os.path.isdir(folder):
            raise HTTPException(status_code=404, detail=f"Folder not found: {folder}")
        result = fs.scan_folder(folder, depth=request.depth)
        return {"folder": folder, **result}

    # ─── Audio system ─────────────────────────────────────

    @app.get("/audio/status")
    async def audio_status():
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            inputs = [i for i, d in enumerate(devices) if d.get("max_input_channels", 0) > 0]
            aec = False
            try:
                from audio_echo import find_loopback_device
                aec = find_loopback_device() is not None
            except Exception:
                aec = False
            return {"devices": len(devices), "input_devices": inputs, "microphone": len(inputs) > 0, "aec_available": aec}
        except Exception as e:
            return {"devices": 0, "microphone": False, "error": str(e)}

    @app.post("/audio/listen")
    async def audio_listen(duration: int = 5, aec: bool = True):
        """Record from the microphone for N seconds and transcribe using a 4-tier STT cascade:
        1. Groq Whisper API (fastest if Groq API key is present)
        2. Google Speech Recognition (free online, no API key required)
        3. OpenAI Whisper API (if OpenAI key is present)
        4. Offline local Whisper model (PyTorch)
        """
        import numpy as np
        import sounddevice as sd
        keys = _sys("api_keys")
        groq_key = keys.get_key("groq") if keys else None
        openai_key = keys.get_key("openai") if keys else None
        rate = 16000
        wav_path = os.path.join(tempfile.gettempdir(), "iris_listen.wav")
        recorded = False
        # Check if AEC can be supported before invoking worker (avoid 2-second subprocess boot lag)
        aec_capable = False
        if aec:
            try:
                import pyaudiowpatch
                aec_capable = True
            except ImportError:
                aec_capable = False

        if aec_capable:
            try:
                worker = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "audio_echo_worker.py"))
                r = subprocess.run(
                    [sys.executable, "-u", worker, str(duration), wav_path],
                    capture_output=True, text=True, timeout=duration + 25, env=os.environ,
                )
                recorded = r.returncode == 0 and os.path.exists(wav_path)
                if not recorded:
                    logger.warning(f"AEC worker failed: {r.stdout.strip()} {r.stderr.strip()}")
            except Exception as e:
                logger.warning(f"AEC worker error: {e}")
        if not recorded:
            try:
                from backend.continuous_voice_daemon import find_best_input_device, resample_audio
                best_dev, native_sr = find_best_input_device()
                audio = sd.rec(int(duration * native_sr), samplerate=native_sr, channels=1, dtype="int16", device=best_dev)
                sd.wait()
                audio_16k = resample_audio(audio.flatten(), native_sr, 16000)
                with wave.open(wav_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(audio_16k.tobytes())
                recorded = os.path.exists(wav_path)
            except Exception as e:
                return {"transcript": "", "text": "", "error": f"Recording failed: {e}", "aec_used": False}

        # ── Tier 1: Groq Whisper API ───────────────────────
        if groq_key:
            try:
                from openai import OpenAI
                client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
                with open(wav_path, "rb") as f:
                    wav_bytes = f.read()
                result = client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=("iris_listen.wav", wav_bytes, "audio/wav"),
                    prompt="Iris, WhatsApp, message, YouTube, automation",
                    temperature=0.0,
                    language="en"
                )
                if result and hasattr(result, "text") and result.text.strip():
                    t_str = result.text.strip()
                    return {"transcript": t_str, "text": t_str, "recorded": wav_path, "aec_used": recorded, "engine": "groq_whisper"}
            except Exception as e:
                logger.warning(f"Groq Whisper transcription failed: {e}")

        # ── Tier 2: SpeechRecognition (Google Free STT) ─────
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data)
                if text and text.strip():
                    t_str = text.strip()
                    return {"transcript": t_str, "text": t_str, "recorded": wav_path, "aec_used": recorded, "engine": "google_stt"}
        except Exception as e:
            logger.warning(f"Google STT failed: {e}")

        # ── Tier 3: OpenAI Whisper API ──────────────────────
        if openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                with open(wav_path, "rb") as f:
                    result = client.audio.transcriptions.create(model="whisper-1", file=f)
                if result and hasattr(result, "text") and result.text.strip():
                    t_str = result.text.strip()
                    return {"transcript": t_str, "text": t_str, "recorded": wav_path, "aec_used": recorded, "engine": "openai_whisper"}
            except Exception as e:
                logger.warning(f"OpenAI Whisper failed: {e}")

        # ── Tier 4: Offline Local Whisper STT ───────────────
        try:
            from stt import WhisperSTT
            stt_engine = WhisperSTT(model_size="small")
            text = stt_engine.transcribe(audio_path=wav_path)
            if text and text.strip():
                t_str = text.strip()
                return {"transcript": t_str, "text": t_str, "recorded": wav_path, "aec_used": recorded, "engine": "local_whisper"}
        except Exception as e:
            logger.warning(f"Local Whisper failed: {e}")

        # ── Tier 5: Windows Native Offline Speech Recognition ───────────────
        try:
            from backend.offline_stt import get_offline_stt
            offline_engine = get_offline_stt()
            text = offline_engine.transcribe_wav_file(wav_path, timeout=6.0)
            if text and text.strip():
                t_str = text.strip()
                return {"transcript": t_str, "text": t_str, "recorded": wav_path, "aec_used": recorded, "engine": "windows_native_offline"}
        except Exception as e:
            logger.warning(f"Windows Native Offline STT failed: {e}")

        return {"transcript": "", "text": "", "error": "No speech detected or transcription engines unavailable", "recorded": wav_path, "aec_used": recorded}

    # ─── Always-On Continuous Voice & Vision Telemetry ───

    @app.get("/voice/listener/status")
    async def voice_listener_status():
        vd = _sys("voice_daemon")
        if vd is None:
            return {"running": False, "status": "offline", "muted": False}
        return vd.get_status()

    @app.post("/voice/listener/toggle")
    async def voice_listener_toggle():
        vd = _sys("voice_daemon")
        if vd is None:
            raise HTTPException(status_code=503, detail="Voice daemon offline")
        new_muted = not vd.muted
        vd.set_muted(new_muted)
        return {"muted": new_muted, "status": "muted" if new_muted else "listening"}

    @app.get("/voice/listener/events")
    async def voice_listener_events(since: float = 0.0):
        vd = _sys("voice_daemon")
        if vd is None:
            return {"events": []}
        return {"events": vd.get_recent_events(since_time=since)}

    @app.get("/vision/continuous/telemetry")
    async def vision_continuous_telemetry():
        vis_d = _sys("vision_daemon")
        if vis_d is None:
            return {"status": "offline"}
        return vis_d.get_latest_context()

    @app.post("/vision/continuous/toggle")
    async def vision_continuous_toggle():
        vis_d = _sys("vision_daemon")
        if vis_d is None:
            raise HTTPException(status_code=503, detail="Vision daemon offline")
        vis_d.enabled = not vis_d.enabled
        return {"enabled": vis_d.enabled, "status": "ok"}


    # ─── Automation system ────────────────────────────────

    @app.get("/automation/status")
    async def automation_status():
        return {
            "available": _sys("task_executor") is not None,
            "app_launcher": _sys("app_launcher") is not None,
            "mouse_keyboard": _sys("mouse_keyboard") is not None,
            "file_ops": _sys("file_ops") is not None,
            "terminal": _sys("terminal") is not None,
            "web_automation": _sys("web_automation") is not None,
            "code_runner": _sys("code_runner") is not None,
            "system_monitor": _sys("system_monitor") is not None,
            "window_manager": _sys("window_manager") is not None,
            "hotkeys": _sys("hotkeys") is not None,
            "safe_mode": getattr(_sys("terminal"), "safe_mode", True),
        }

    @app.get("/automation/apps")
    async def automation_apps():
        launcher = _sys("app_launcher")
        if not launcher:
            return {"success": False, "error": "app launcher not available"}
        apps = launcher.list_apps()
        return {"success": True, "count": len(apps), "apps": apps}

    @app.get("/code/status")
    async def code_status():
        cr = _sys("code_runner")
        if cr is None:
            raise HTTPException(status_code=503, detail="Code runner not available")
        return cr.get_status()

    @app.post("/automation/launch")
    async def automation_launch(request: LaunchRequest):
        launcher = _sys("app_launcher")
        if launcher is None:
            raise HTTPException(status_code=503, detail="App launcher not available")
        result = launcher.launch(request.app, request.args)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "launch failed"))
        return result

    @app.post("/automation/run-command")
    async def automation_run_command(request: CommandRequest):
        terminal = _sys("terminal")
        if terminal is None:
            raise HTTPException(status_code=503, detail="Terminal not available")
        result = terminal.execute(request.command)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "command failed"))
        return result

    # ─── Full system diagnostic ───────────────────────────

    @app.get("/test/all")
    async def test_all():
        report = {}

        def run(name: str, fn):
            try:
                report[name] = {"status": "pass", **fn()}
            except Exception as e:
                report[name] = {"status": "fail", "error": str(e)[:300]}

        def t_core():
            return {
                "name": brain.name,
                "awake": brain.is_awake,
                "mode": brain.get_mode(),
                "memory": brain._memory is not None,
                "voice": brain._voice is not None,
                "vision": brain._vision is not None,
                "hands": brain._hands is not None,
                "model_router": brain._model_router is not None,
            }

        def t_think():
            result = brain.think("Hello Iris, introduce yourself in one sentence.")
            return {"reply": (result.get("text", "") or "")[:120], "intent": result.get("intent")}

        def t_memory():
            mem = _sys("memory")
            key = f"test_{int(time.time())}"
            mem.store(key, "diagnostic memory entry", permanent=True)
            recalled = mem.get(key)
            return {"key": key, "stored": True, "recalled": bool(recalled), "recalled_value": (recalled or "")[:60] if isinstance(recalled, str) else str(recalled or "")[:60]}

        def t_voice():
            voice = _voice_holder["engine"]
            status = voice.get_status() if voice else {"error": "no engine"}
            if voice:
                voice.speak("Voice system test. Can you hear me?")
            return {"engine": status.get("voice"), "speaking": status.get("speaking")}

        def t_vision():
            ss = _sys("screenshot")
            path = ss.capture() if ss and ss.is_enabled() else None
            return {"screenshot_captured": bool(path), "path": os.path.abspath(path) if path else None,
                    "ocr": _sys("ocr").get_status() if _sys("ocr") else {"available": False}}

        def t_audio():
            try:
                import sounddevice as sd
                devices = sd.query_devices()
                inputs = [i for i, d in enumerate(devices) if d.get("max_input_channels", 0) > 0]
                return {"microphone_devices": len(inputs), "total_devices": len(devices)}
            except Exception as e:
                return {"microphone_devices": 0, "error": str(e)}

        def t_automation():
            launcher = _sys("app_launcher")
            terminal = _sys("terminal")
            running = launcher.list_running() if launcher and hasattr(launcher, "list_running") else []
            return {
                "launcher_ready": launcher is not None,
                "terminal_ready": terminal is not None,
                "safe_mode": getattr(terminal, "safe_mode", True),
                "running_apps": len(running or []),
            }

        def t_api_keys():
            keys = _sys("api_keys")
            if not keys:
                return {"count": 0}
            return {"count": keys.key_count() if hasattr(keys, "key_count") else 0,
                    "providers": keys.providers_available() if hasattr(keys, "providers_available") else []}

        run("core", t_core)
        run("think", t_think)
        run("memory", t_memory)
        run("voice", t_voice)
        run("vision", t_vision)
        run("audio", t_audio)
        run("automation", t_automation)
        run("api_keys", t_api_keys)

        passed = sum(1 for v in report.values() if v.get("status") == "pass")
        return {"summary": {"passed": passed, "total": len(report), "all_pass": passed == len(report)}, "report": report}

    # ─── Legacy / agent endpoints ─────────────────────────

    @app.post("/think", response_model=ChatResponse)
    def think(request: ChatRequest):
        return chat(request)

    # ─── Full-Duplex WebRTC Audio Transport & Streaming Subsystems ───────

    @app.websocket("/ws/audio")
    async def websocket_audio_endpoint(websocket: WebSocket):
        """
        Real-time full-duplex bidirectional audio transport endpoint.
        Transfers microphone PCM chunks, performs real-time noise suppression & Silero VAD,
        triggers instant barge-in, and streams assistant tokens & audio chunks back.
        """
        # Security: verify local loopback origin to protect voice sessions
        client_host = websocket.client.host if websocket.client else ""
        if client_host and client_host not in ("127.0.0.1", "localhost", "::1", "testclient"):
            logger.warning(f"Unauthorized remote WebSocket connection attempt from {client_host}")
            await websocket.close(code=1008)
            return

        await websocket.accept()
        session = create_or_get_session(
            voice_engine=_voice_holder.get("engine"),
            api_keys=_sys("api_keys"),
        )
        logger.info(f"🎙️ Full-duplex WebSocket audio session established: [{session.session_id}]")

        # Send initial connection handshake
        await websocket.send_json({
            "type": "session_init",
            "session_id": session.session_id,
            "sample_rate": session.sample_rate,
            "vad_threshold": session.vad.threshold,
            "noise_suppression": session.noise_suppressor.level_name,
            "status": "connected",
        })

        # Register barge-in listener to immediately broadcast interruption frames
        loop = asyncio.get_event_loop()
        def on_barge_in_broadcast(stopped_id: str, latency_ms: float):
            try:
                coro = websocket.send_json({
                    "type": "barge_in",
                    "stopped_generation_id": stopped_id,
                    "latency_ms": round(latency_ms, 2),
                    "timestamp": time.time(),
                })
                asyncio.run_coroutine_threadsafe(coro, loop)
            except Exception:
                pass

        session.barge_in_mgr.add_listener(on_barge_in_broadcast)

        try:
            while True:
                message = await websocket.receive()
                if "bytes" in message and message["bytes"]:
                    pcm_data = message["bytes"]
                    events = session.process_incoming_pcm(pcm_data)

                    # Send VAD telemetry every 5 frames (~160ms)
                    if session.frames_received % 5 == 0 and events.get("vad"):
                        await websocket.send_json({
                            "type": "vad_telemetry",
                            "is_speech": events["vad"]["is_speech"],
                            "confidence": events["vad"]["probability"],
                            "noise_power_db": float(session.noise_suppressor.noise_power_db),
                            "session_id": session.session_id,
                        })

                    # If end of utterance detected, transcribe and answer
                    if events.get("utterance_ready"):
                        await websocket.send_json({"type": "transcribing"})
                        wav_bytes = session.get_accumulated_wav_bytes()
                        user_text = session.transcribe_utterance(wav_bytes)

                        if user_text:
                            await websocket.send_json({
                                "type": "user_transcript",
                                "text": user_text,
                                "session_id": session.session_id,
                            })

                            # Stream response back across websocket
                            await _stream_assistant_response_ws(websocket, session, user_text)

                elif "text" in message and message["text"]:
                    data = json.loads(message["text"])
                    action = data.get("action", "")

                    if action == "chat":
                        user_text = data.get("message", "")
                        if user_text:
                            await _stream_assistant_response_ws(websocket, session, user_text)

                    elif action == "barge_in":
                        record = session.barge_in_mgr.trigger_barge_in(source="websocket_client")
                        await websocket.send_json({
                            "type": "barge_in_ack",
                            "stopped_generation_id": record.get("interrupted_generation_id"),
                            "latency_ms": record.get("latency_ms"),
                        })

                    elif action == "configure_vad":
                        th = data.get("threshold")
                        nth = data.get("neg_threshold")
                        session.vad.set_thresholds(threshold=th, neg_threshold=nth)
                        await websocket.send_json({
                            "type": "vad_config_ack",
                            "threshold": session.vad.threshold,
                            "neg_threshold": session.vad.neg_threshold,
                        })

                    elif action == "configure_noise":
                        lvl = data.get("level", "moderate")
                        ok = session.noise_suppressor.set_level(lvl)
                        await websocket.send_json({
                            "type": "noise_config_ack",
                            "level": session.noise_suppressor.level_name,
                            "success": ok,
                        })

                    elif action == "ping":
                        await websocket.send_json({"type": "pong", "time": time.time()})

        except (WebSocketDisconnect, RuntimeError) as e:
            logger.info(f"Full-duplex WebSocket client session ended: [{session.session_id}] ({e})")
        except Exception as e:
            logger.error(f"Full-duplex WebSocket session error: {e}")
        finally:
            remove_session(session.session_id)

    async def _stream_assistant_response_ws(websocket: WebSocket, session: FullDuplexAudioSession, user_text: str):
        """Helper to stream LLM tokens and incremental TTS audio chunks across WebSocket."""
        session.is_iris_speaking = True
        session.iris_speech_started_at = time.time()
        session.consecutive_interruption_frames = 0
        loop = asyncio.get_event_loop()

        def ws_on_token(token: str, gen_id: str):
            try:
                coro = websocket.send_json({
                    "type": "token",
                    "token": token,
                    "generation_id": gen_id,
                })
                asyncio.run_coroutine_threadsafe(coro, loop)
            except Exception:
                pass

        def ws_on_audio_chunk(chunk_payload: dict):
            try:
                audio_file = chunk_payload.get("audio_path")
                b64_audio = ""
                if audio_file and os.path.exists(audio_file):
                    with open(audio_file, "rb") as af:
                        b64_audio = base64.b64encode(af.read()).decode("ascii")

                coro = websocket.send_json({
                    "type": "audio_chunk",
                    "chunk_index": chunk_payload.get("chunk_index"),
                    "audio_base64": b64_audio,
                    "text": chunk_payload.get("text"),
                    "generation_id": chunk_payload.get("generation_id"),
                    "is_final": chunk_payload.get("is_final"),
                })
                asyncio.run_coroutine_threadsafe(coro, loop)
            except Exception as ce:
                logger.debug(f"Audio chunk WS dispatch error: {ce}")

        # Send response start indicator
        await websocket.send_json({"type": "assistant_start", "query": user_text})

        # Run stream in background executor thread
        messages = [{"role": "user", "content": user_text}]
        res = await asyncio.to_thread(
            session.streaming_orch.stream_chat_and_synthesize,
            messages=messages,
            synthesize_voice=True,
            on_token=ws_on_token,
            on_audio_chunk=ws_on_audio_chunk,
        )

        session.is_iris_speaking = False
        await websocket.send_json({
            "type": "assistant_done",
            "generation_id": res.get("generation_id"),
            "full_response": res.get("response"),
            "metrics": res.get("metrics"),
            "interrupted": res.get("interrupted"),
        })

    # ─── WebRTC Signaling Endpoints ─────────────────────────────────────

    @app.post("/webrtc/offer")
    async def webrtc_offer(request: Request):
        """
        WebRTC SDP Offer negotiation endpoint.
        Initializes session and returns compatible answer/session configuration.
        """
        data = await request.json()
        sdp_offer = data.get("sdp", "")
        session_id = data.get("session_id") or f"rtc-{uuid.uuid4().hex[:8]}"

        session = create_or_get_session(
            session_id=session_id,
            voice_engine=_voice_holder.get("engine"),
            api_keys=_sys("api_keys"),
        )
        logger.info(f"WebRTC offer received for session [{session.session_id}]")

        # In standard Chromium WebView2 architecture, audio streams bridge via
        # high-performance binary WebSocket (/ws/audio) with WebRTC session signaling
        return {
            "status": "ready",
            "session_id": session.session_id,
            "sdp_type": "answer",
            "sdp": f"v=0\r\no=IRIS 0 0 IN IP4 127.0.0.1\r\ns=FullDuplexSession\r\nt=0 0\r\na=sendrecv\r\n",
            "transport": "websocket_binary_fallback",
            "ws_endpoint": f"ws://127.0.0.1:5743/ws/audio?session_id={session.session_id}",
            "vad_threshold": session.vad.threshold,
            "noise_suppression": session.noise_suppressor.level_name,
        }

    @app.post("/webrtc/ice")
    async def webrtc_ice(request: Request):
        """WebRTC ICE Candidate exchange handler."""
        data = await request.json()
        session_id = data.get("session_id", "default")
        candidate = data.get("candidate")
        logger.debug(f"Received ICE candidate for session [{session_id}]: {candidate}")
        return {"status": "ok", "session_id": session_id}

    @app.get("/webrtc/status")
    async def webrtc_status():
        """Monitor active WebRTC and full-duplex audio communication sessions."""
        return {
            "status": "active",
            "active_sessions": get_all_sessions_status(),
            "total_active_sessions": len(get_all_sessions_status()),
        }

    # ─── Silero VAD & Noise Suppression Control Endpoints ────────────────

    @app.get("/audio/vad/status")
    async def audio_vad_status():
        """Retrieve real-time Silero VAD diagnostics and state."""
        vad = get_silero_vad()
        return vad.get_diagnostics()

    @app.post("/audio/vad/config")
    async def audio_vad_config(data: dict):
        """Configure Silero VAD detection thresholds."""
        vad = get_silero_vad()
        th = data.get("threshold")
        nth = data.get("neg_threshold")
        msp = data.get("min_speech_duration_ms")
        msl = data.get("min_silence_duration_ms")
        vad.set_thresholds(threshold=th, neg_threshold=nth, min_speech_duration_ms=msp, min_silence_duration_ms=msl)
        return {"success": True, "diagnostics": vad.get_diagnostics()}

    @app.get("/audio/noise-suppression/status")
    async def audio_noise_suppression_status():
        """Retrieve real-time noise suppression statistics."""
        ns = get_noise_suppressor()
        return ns.get_stats()

    @app.post("/audio/noise-suppression/config")
    async def audio_noise_suppression_config(data: dict):
        """Set real-time noise suppression level ('off', 'low', 'moderate', 'high')."""
        ns = get_noise_suppressor()
        level = data.get("level", "moderate")
        ok = ns.set_level(level)
        return {"success": ok, "stats": ns.get_stats()}

    # ─── Barge-In Control & Status Endpoints ─────────────────────────────

    @app.get("/barge-in/status")
    async def barge_in_status():
        """Retrieve barge-in and response cancellation telemetry."""
        bm = get_barge_in_manager()
        return bm.get_status()

    @app.post("/barge-in/trigger")
    async def barge_in_trigger(data: Optional[dict] = None):
        """Immediately trigger barge-in and cancel active assistant response."""
        source = (data or {}).get("source", "api_trigger")
        bm = get_barge_in_manager(_voice_holder.get("engine"))
        record = bm.trigger_barge_in(source=source)
        return {"success": True, "record": record}

    # ─── Streaming Chat (SSE Token Stream) ────────────────────────────────

    @app.post("/chat/stream")
    async def chat_stream_endpoint(request: ChatRequest):
        """
        Server-Sent Events (SSE) token streaming endpoint.
        Streams partial tokens as text/event-stream chunks to UI.
        """
        router = _sys("hybrid_router")
        if router is None:
            from backend.engine.hybrid_model_router import get_hybrid_router
            router = get_hybrid_router(_sys("api_keys"))

        orch = get_streaming_orchestrator(hybrid_router=router, voice_engine=_voice_holder.get("engine"))

        async def sse_generator():
            token_queue = asyncio.Queue()
            loop = asyncio.get_event_loop()

            def on_tok(tok, gid):
                loop.call_soon_threadsafe(token_queue.put_nowait, {"type": "token", "token": tok, "gen_id": gid})

            def on_chunk(chk):
                loop.call_soon_threadsafe(token_queue.put_nowait, {"type": "chunk", "text": chk.get("text")})

            def run_stream():
                res = orch.stream_chat_and_synthesize(
                    messages=[{"role": "user", "content": request.message}],
                    synthesize_voice=bool(request.voice),
                    on_token=on_tok,
                    on_audio_chunk=on_chunk,
                )
                loop.call_soon_threadsafe(token_queue.put_nowait, {"type": "done", "metrics": res.get("metrics")})

            threading.Thread(target=run_stream, daemon=True).start()

            while True:
                item = await token_queue.get()
                yield f"data: {json.dumps(item)}\n\n"
                if item.get("type") == "done":
                    break

        return StreamingResponse(sse_generator(), media_type="text/event-stream")

    return app


app = create_app()
