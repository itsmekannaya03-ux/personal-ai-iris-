"""
IGRIS — Integrated General Response Intelligence System

The 5-system architecture:
  core/     → thinks and decides
  memory/   → three-layer memory
  voice/    → emotional speech
  vision/   → sees the screen
  hands/    → performs actions

This module wires all 5 systems together into one unified brain.
"""

import logging
import time
import threading
from typing import Optional, Callable

from core import IrisBrain, IntentDetector, Decider, IrisPersonality, ModelRouter
from memory import TempLayer, LongTempLayer, DeepLayer, MemoryOrchestrator, MemoryCommands
from voice import TTSEngine, EmotionDetector, EmotionMapper, VoicePresets, VoiceBiometrics
from vision import ScreenshotCapture, OCREngine, ImageAnalyzer, VideoScanner, FileScanner, UIDetector
from hands import AppLauncher, MouseKeyboard, FileOps, TerminalExecutor, WebAutomation, TaskExecutor

logger = logging.getLogger("igris")


class IGRIS:
    """
    Main IGRIS system — wires all 5 subsystems together.

    Usage:
        igris = IGRIS()
        igris.initialize()
        result = igris.think("Hello")
        igris.speak(result["text"])
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.initialized = False

        # System 1: Core
        self.brain: Optional[IrisBrain] = None
        self.intent: Optional[IntentDetector] = None
        self.decider: Optional[Decider] = None
        self.personality: Optional[IrisPersonality] = None
        self.model_router: Optional[ModelRouter] = None

        # System 2: Memory
        self.temp_layer: Optional[TempLayer] = None
        self.long_temp_layer: Optional[LongTempLayer] = None
        self.deep_layer: Optional[DeepLayer] = None
        self.memory_orchestrator: Optional[MemoryOrchestrator] = None
        self.memory_commands: Optional[MemoryCommands] = None

        # System 3: Voice
        self.tts_engine: Optional[TTSEngine] = None
        self.emotion_detector: Optional[EmotionDetector] = None
        self.emotion_mapper: Optional[EmotionMapper] = None
        self.voice_presets: Optional[VoicePresets] = None
        self.voice_biometrics: Optional[VoiceBiometrics] = None

        # System 4: Vision
        self.screenshot: Optional[ScreenshotCapture] = None
        self.ocr: Optional[OCREngine] = None
        self.image_analyzer: Optional[ImageAnalyzer] = None
        self.video_scanner: Optional[VideoScanner] = None
        self.file_scanner: Optional[FileScanner] = None
        self.ui_detector: Optional[UIDetector] = None

        # System 5: Hands
        self.app_launcher: Optional[AppLauncher] = None
        self.mouse_keyboard: Optional[MouseKeyboard] = None
        self.file_ops: Optional[FileOps] = None
        self.terminal: Optional[TerminalExecutor] = None
        self.web_automation: Optional[WebAutomation] = None
        self.task_executor: Optional[TaskExecutor] = None

        # Callbacks
        self.on_response: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

    def initialize(self):
        """Initialize all 5 systems in dependency order."""
        logger.info("=" * 50)
        logger.info("IGRIS — Initializing all 5 systems")
        logger.info("=" * 50)

        self._init_memory()
        self._init_core()
        self._init_voice()
        self._init_vision()
        self._init_hands()
        self._wire_cross_connections()

        self.initialized = True
        logger.info("IGRIS — All systems ready")

    def _init_memory(self):
        logger.info("[Memory] Initializing three-layer memory...")
        self.temp_layer = TempLayer()
        self.long_temp_layer = LongTempLayer()
        self.deep_layer = DeepLayer()
        self.memory_orchestrator = MemoryOrchestrator(self.temp_layer, self.long_temp_layer, self.deep_layer)
        self.memory_commands = MemoryCommands(self.memory_orchestrator)
        logger.info(f"[Memory] Ready — Temp: {self.temp_layer.get_count()}, Long: {self.long_temp_layer.get_count()}, Deep: {self.deep_layer.get_count()}")

    def _init_core(self):
        logger.info("[Core] Initializing thinking engine...")
        self.personality = IrisPersonality(self.config.get("personality", {}))
        self.intent = IntentDetector()
        self.decider = Decider()
        self.model_router = ModelRouter()
        self.brain = IrisBrain(self.config.get("brain", {}))
        self.brain.set_intent(self.intent)
        self.brain.set_decider(self.decider)
        self.brain.set_personality(self.personality)
        self.brain.set_model_router(self.model_router)
        self.brain.set_memory(self.memory_orchestrator)
        logger.info("[Core] Ready")

    def _init_voice(self):
        logger.info("[Voice] Initializing speech system...")
        self.emotion_detector = EmotionDetector()
        self.emotion_mapper = EmotionMapper()
        self.voice_presets = VoicePresets()
        self.voice_biometrics = VoiceBiometrics()
        self.tts_engine = TTSEngine(
            backend=self.config.get("tts_backend", "default"),
            voice_presets=self.voice_presets,
            emotion_mapper=self.emotion_mapper,
        )
        self.brain.set_voice(self.tts_engine)
        logger.info("[Voice] Ready")

    def _init_vision(self):
        logger.info("[Vision] Initializing visual system...")
        vision_enabled = self.config.get("vision_enabled", False)
        self.screenshot = ScreenshotCapture(enabled=vision_enabled)
        self.ocr = OCREngine()
        self.image_analyzer = ImageAnalyzer()
        self.video_scanner = VideoScanner(image_analyzer=self.image_analyzer)
        self.file_scanner = FileScanner()
        self.ui_detector = UIDetector(ocr_engine=self.ocr)
        self.brain.set_vision(self.screenshot)
        logger.info("[Vision] Ready")

    def _init_hands(self):
        logger.info("[Hands] Initializing action system...")
        self.app_launcher = AppLauncher()
        self.mouse_keyboard = MouseKeyboard()
        self.file_ops = FileOps()
        self.terminal = TerminalExecutor(safe_mode=self.config.get("safe_mode", True))
        self.web_automation = WebAutomation()
        self.task_executor = TaskExecutor(
            app_launcher=self.app_launcher,
            mouse_keyboard=self.mouse_keyboard,
            file_ops=self.file_ops,
            terminal=self.terminal,
            web_automation=self.web_automation,
        )
        self.decider.set_hands(self.task_executor)
        self.brain.set_hands(self.task_executor)
        logger.info("[Hands] Ready")

    def _wire_cross_connections(self):
        self.video_scanner.set_image_analyzer(self.image_analyzer)
        self.ui_detector.set_ocr(self.ocr)

    # ─── Public API ───────────────────────────────────────────

    def think(self, text: str) -> dict:
        if not self.initialized:
            return {"text": "IGRIS is not initialized. Call igris.initialize() first.", "action": "error"}
        result = self.brain.think(text)
        if self.on_response:
            self.on_response(result.get("text", ""))
        return result

    def think_async(self, text: str, callback: Optional[Callable] = None):
        self.brain.think_async(text, callback)

    def speak(self, text: str, preset: Optional[str] = None):
        if not self.initialized:
            return
        emotion_data = self.emotion_detector.detect(text)
        self.tts_engine.speak(
            text=text,
            emotion=emotion_data.get("emotion", "neutral"),
            confidence=emotion_data.get("confidence", 0.8),
            preset=preset,
        )

    def process(self, text: str, speak: bool = True) -> dict:
        result = self.think(text)
        if speak and result.get("text"):
            self.speak(result["text"])
        return result

    def wake(self):
        self.brain.wake()

    def sleep(self):
        self.brain.sleep()

    def set_mode(self, mode: str):
        self.brain.set_mode(mode)

    def get_mode(self) -> str:
        return self.brain.get_mode()

    def status(self) -> dict:
        if not self.initialized:
            return {"initialized": False}
        return {
            "initialized": True,
            **self.brain.status(),
            "memory": self.memory_orchestrator.get_stats(),
            "voice": self.tts_engine.get_status(),
            "voice_presets": self.voice_presets.get_status(),
            "voice_biometrics": self.voice_biometrics.get_status(),
            "vision_enabled": self.screenshot.is_enabled() if self.screenshot else False,
        }

    # ─── Memory convenience methods ───────────────────────────

    def remember(self, key: str, content: str, permanent: bool = False):
        return self.memory_orchestrator.store(key, content, permanent)

    def recall(self, query: str) -> dict:
        if self.memory_commands:
            return self.memory_commands._recall(query)
        return self.memory_orchestrator.recall_relevant(query)

    def forget(self, key: str) -> bool:
        return self.memory_orchestrator.delete(key)

    def run_maintenance(self):
        self.memory_orchestrator.run_maintenance()
