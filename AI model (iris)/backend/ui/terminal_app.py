import logging
import time
import sys
import os
import threading
import re

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _BACKEND)
sys.path.insert(0, _ROOT)

logger = logging.getLogger("iris.ui.terminal")

WAKE_PATTERNS = [
    re.compile(r'^weak up([,.!\s]|$)', re.IGNORECASE),
    re.compile(r'^wake up([,.!\s]|$)', re.IGNORECASE),
    re.compile(r'^hey iris([,.!\s]|$)', re.IGNORECASE),
    re.compile(r'^hello iris([,.!\s]|$)', re.IGNORECASE),
    re.compile(r'^iris([,.!\s]|$)', re.IGNORECASE),
]


def _contains_wake_word(text: str) -> bool:
    return any(p.search(text) for p in WAKE_PATTERNS)


def _strip_wake_word(text: str) -> str:
    for p in WAKE_PATTERNS:
        text = p.sub("", text).strip()
    return text


class TerminalApp:
    FACE_W = 60

    def __init__(self):
        self._running = False
        self._face = None
        self._sound_bar = None
        self._camera = None
        self._voice = None
        self._brain = None
        self._memory_orch = None

        self._user_input_buffer = ""
        self._thinking = False
        self._wake_triggered = False

        self._chat_history: list[dict] = []
        self._face_lines: list[str] = []
        self._last_response_time = 0.0

    def initialize(self):
        logger.info("Initializing TerminalApp...")

        from core import IrisBrain, IntentDetector, Decider, IrisPersonality, ModelRouter
        from memory import TempLayer, LongTempLayer, DeepLayer, MemoryOrchestrator
        from voice import EmotionDetector, EmotionMapper, VoicePresets
        from vision import FileScanner
        from hands import AppLauncher, FileOps, WebAutomation

        self._personality = IrisPersonality({"name": "Iris", "style": "friendly"})
        self._intent = IntentDetector()
        self._decider = Decider()
        self._router = ModelRouter()
        self._memory_orch = MemoryOrchestrator(TempLayer(), LongTempLayer(), DeepLayer())
        self._brain = IrisBrain()
        self._brain.set_intent(self._intent)
        self._brain.set_decider(self._decider)
        self._brain.set_personality(self._personality)
        self._brain.set_model_router(self._router)
        self._brain.set_memory(self._memory_orch)

        self._memory_orch.store_permanent("user_identity", "young master",
                                          {"type": "identity", "source": "user"})

        self._emotion = EmotionDetector()
        self._voice_presets = VoicePresets()
        self._file_scanner = FileScanner()
        self._app_launcher = AppLauncher()
        self._file_ops = FileOps()
        self._web = WebAutomation()

        from backend.voice_engine import VoiceEngine
        self._voice = VoiceEngine(voice="sweet")

        from .terminal_face import TerminalFace
        from .sound_bar import SoundBar
        from .camera_listener import CameraListener
        self._face = TerminalFace()
        self._sound_bar = SoundBar()
        self._camera = CameraListener()

        self._sound_bar.start()
        self._camera.start()

        self._add_chat("iris", "Hello young master! I'm Iris, your AI assistant.")
        logger.info("TerminalApp initialized")

    def start(self):
        self._running = True
        self._render_static()
        self._terminal_loop()

    def stop(self):
        self._running = False
        if self._sound_bar:
            self._sound_bar.stop()
        if self._camera:
            self._camera.stop()

    def _add_chat(self, role: str, text: str):
        self._chat_history.append({"role": role, "text": text})
        if len(self._chat_history) > 50:
            self._chat_history = self._chat_history[-50:]

    def _render_static(self):
        import shutil
        cols = shutil.get_terminal_size().columns
        lw = cols - self.FACE_W - 2

        lines = []
        lines.append("")
        lines.append("=" * cols)
        lines.append("  IRIS - IGRIS Terminal Interface".center(cols))
        lines.append("=" * cols)
        lines.append("")

        chat_panel = self._build_chat_panel(cols)
        self._face_lines = self._face.render_frame(self.FACE_W)
        combined = self._combine_panels(chat_panel, cols)
        lines.extend(combined)

        lines.append("")
        bar = self._sound_bar.render_bar(cols)
        lines.append(bar)
        lines.append(self._get_camera_summary())
        lines.append(self._get_status_line())
        lines.append("")
        lines.append("  > ")

        self._static_top = len(lines) + 1
        print("\n".join(lines))

    def _build_chat_panel(self, cols: int) -> list[str]:
        lw = cols - self.FACE_W - 2
        chat_h = len(self._face_lines) if self._face_lines else 14
        panel = []
        for msg in reversed(self._chat_history):
            prefix = "master:" if msg["role"] == "master" else "iris:"
            max_text_w = lw - len(prefix) - 3
            text = msg["text"]
            if len(text) > max_text_w:
                words = text.split()
                cur = ""
                for w in words:
                    candidate = cur + (" " if cur else "") + w
                    if len(candidate) > max_text_w:
                        panel.append(f"  {prefix} {cur}")
                        cur = w
                    else:
                        cur = candidate
                if cur:
                    panel.append(f"  {prefix} {cur}")
            else:
                panel.append(f"  {prefix} {text}")
            if len(panel) >= chat_h:
                break
        panel.reverse()
        while len(panel) < chat_h:
            panel.insert(0, "")
        return panel

    def _combine_panels(self, chat_panel: list[str], cols: int) -> list[str]:
        lw = cols - self.FACE_W - 2
        face_panel = self._face_lines
        max_h = max(len(chat_panel), len(face_panel))
        result = []
        for i in range(max_h):
            left = chat_panel[i] if i < len(chat_panel) else ""
            right = face_panel[i] if i < len(face_panel) else ""
            left = left.ljust(lw)
            right = right.ljust(self.FACE_W)
            result.append(left + "  " + right)
        return result

    def _render_dynamic(self):
        import shutil
        cols = shutil.get_terminal_size().columns
        lw = cols - self.FACE_W - 2

        self._update_mood_from_context()
        self._face_lines = self._face.render_frame(self.FACE_W)
        chat_panel = self._build_chat_panel(cols)
        combined = self._combine_panels(chat_panel, cols)

        ansi = ""
        ansi += f"\033[{self._static_top}A"

        for line in combined:
            ansi += "\r\033[K" + line + "\n"

        now = time.time()
        if self._last_response_time > 0 and now - self._last_response_time < 10:
            ansi += "\r\033[K  " + self._pending_response + "\n"
        else:
            ansi += "\r\033[K\n"

        bar = self._sound_bar.render_bar(cols)
        ansi += "\r\033[K" + bar + "\n"

        ansi += "\r\033[K" + self._get_camera_summary() + "\n"
        ansi += "\r\033[K" + self._get_status_line() + "\n"
        ansi += "\r\033[K\n"
        ansi += "\r\033[K  > " + self._user_input_buffer

        sys.stdout.write(ansi)
        sys.stdout.flush()

    def _terminal_loop(self):
        self._pending_response = ""
        self._last_response_time = 0.0

        try:
            while self._running:
                self._render_dynamic()
                self._check_voice_for_wake()
                if self._check_stdin():
                    self._handle_input(self._user_input_buffer.strip())
                time.sleep(0.08)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
            print("\nIris: Goodbye young master! I'll be here when you need me.")

    def _check_voice_for_wake(self):
        if not self._sound_bar or self._thinking or self._wake_triggered:
            return
        if self._sound_bar.is_voice_active():
            ratio = self._sound_bar.get_voice_ratio()
            if ratio > 0.3:
                self._wake_triggered = True
                self._pending_response = "I heard you young master! Type your command:"
                self._last_response_time = time.time()

    def _get_status_line(self) -> str:
        parts = [
            "[HEART]",
            (">AWAKE" if self._brain and self._brain.is_awake else ">STANDBY"),
            ">>" + (self._brain.get_mode().upper() if self._brain else "N/A"),
        ]
        if self._camera:
            parts.append("(CAM)" + ("FACE" if self._camera.is_face_detected() else "NO FACE"))
        if self._sound_bar:
            parts.append("(MIC)" + ("VOICE" if self._sound_bar.is_voice_active() else "SILENT"))
        if self._voice:
            parts.append("(SPK)" + ("SPEAKING" if self._voice.is_speaking() else "IDLE"))
        return "  " + " | ".join(parts)

    def _get_camera_summary(self) -> str:
        if not self._camera or not self._camera.is_face_detected():
            return "  CAMERA: No face detected"
        mood = self._camera.infer_user_mood()
        looking = "looking" if self._camera.is_looking() else "looking away"
        speaking = "speaking" if self._camera.is_user_speaking() else "silent"
        return f"  CAM: {mood.upper()} | {looking} | {speaking} | smile:{self._camera.get_smile():.0%}"

    def _update_mood_from_context(self):
        if not self._camera or not self._sound_bar:
            return
        cam_mood = self._camera.infer_user_mood()
        if self._sound_bar.is_voice_active() or self._camera.is_user_speaking():
            mood = "happy" if cam_mood == "happy" else "excited"
        elif self._voice and self._voice.is_speaking():
            mood = "happy"
        elif self._thinking:
            mood = "thinking"
        elif cam_mood == "sad":
            mood = "sad"
        else:
            mood = "neutral"
        self._face.set_mood(mood)

    def _check_stdin(self) -> bool:
        import select
        if sys.platform == "win32":
            import msvcrt
            if msvcrt.kbhit():
                char = msvcrt.getwche()
                if char == "\r":
                    self._user_input_buffer += "\n"
                    return True
                elif char == "\b":
                    self._user_input_buffer = self._user_input_buffer[:-1]
                else:
                    self._user_input_buffer += char
            return False
        else:
            if select.select([sys.stdin], [], [], 0)[0]:
                char = sys.stdin.read(1)
                if char == "\n":
                    return True
                self._user_input_buffer += char
            return False

    def _handle_input(self, text: str):
        self._user_input_buffer = ""
        self._wake_triggered = False
        if not text:
            return

        lower = text.lower()
        if lower in ("exit", "quit"):
            self._running = False
            return

        if _contains_wake_word(text):
            clean = _strip_wake_word(text)
            if clean:
                text = clean
            else:
                self._add_chat("master", text)
                self._add_chat("iris", "I'm awake young master! Ask me anything.")
                return

        self._add_chat("master", text)
        self._thinking = True
        self._face.set_mood("thinking")

        def process():
            result = self._brain.think(text)
            response = result.get("text", "")
            self._add_chat("iris", response)
            self._thinking = False
            if self._voice:
                self._voice.speak(response)
            self._face.set_speaking(True)
            threading.Timer(0.5, lambda: self._face.set_speaking(False)).start()

        threading.Thread(target=process, daemon=True).start()

    def get_status(self) -> dict:
        return {"running": self._running}
