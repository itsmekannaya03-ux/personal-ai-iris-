"""
Continuous Vision Daemon for IRIS AI
====================================
Always-on visual intelligence:
1. Camera Stream: Continuous presence, single-owner biometric recognition,
   emotion classification, and lip dynamics via PresenceEmotionEngine.
2. Ambient Screen Stream: Continuous foreground window monitoring & background
   lightweight screen perception.
3. Pre-cached Visual Context: When the user asks "What's on my screen?" or
   "What am I doing?", Iris responds instantly without delay.
4. Proactive Visual Help: Automatically detects errors or code focus and offers
   assistance when appropriate.
"""

import os
import re
import time
import logging
import threading
from typing import Optional, Dict, Any, List

logger = logging.getLogger("iris.vision_daemon")


class ContinuousVisionDaemon:
    """
    Manages continuous ambient visual perception across Camera and Screen.
    """

    def __init__(
        self,
        presence_emotion_engine=None,
        screenshot_engine=None,
        ocr_engine=None,
        window_manager=None,
        scan_interval: float = 8.0,
    ):
        self.presence_engine = presence_emotion_engine
        self.screenshot_engine = screenshot_engine
        self.ocr_engine = ocr_engine
        self.window_manager = window_manager
        self.scan_interval = scan_interval

        self.enabled = True
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Latest Visual Intelligence Context
        self._context_lock = threading.Lock()
        self._latest_context: Dict[str, Any] = {
            "camera_active": False,
            "user_detected": False,
            "is_owner": False,
            "user_name": "Commander",
            "emotion": "neutral",
            "confidence": 0.0,
            "is_lips_moving": False,
            "is_away": False,
            "active_window": "",
            "activity_type": "Idle",
            "screen_summary": "",
            "has_error": False,
            "error_detail": "",
            "last_screen_scan": 0.0,
            "timestamp": time.time(),
        }

        self._last_window = ""

    def start(self):
        """Start the continuous vision monitor."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="IrisContinuousVisionDaemon")
        self._thread.start()
        logger.info("👁️ Always-On Continuous Vision Daemon activated.")

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Continuous Vision Daemon stopped.")

    def get_latest_context(self) -> Dict[str, Any]:
        """Return fresh snapshot of camera & screen visual intelligence."""
        with self._context_lock:
            # Refresh camera sub-fields dynamically if engine is running
            if self.presence_engine and hasattr(self.presence_engine, "get_current_state"):
                try:
                    st = self.presence_engine.get_current_state()
                    self._latest_context["camera_active"] = getattr(self.presence_engine, "is_enabled", lambda: True)()
                    self._latest_context["user_detected"] = bool(getattr(st, "user_detected", False))
                    self._latest_context["is_owner"] = bool(getattr(st, "is_owner", False))
                    self._latest_context["user_name"] = getattr(st, "user_name", "Commander")
                    self._latest_context["emotion"] = getattr(st, "emotion", "neutral")
                    self._latest_context["confidence"] = round(float(getattr(st, "confidence", 0.0)), 2)
                    self._latest_context["is_lips_moving"] = bool(getattr(st, "is_lips_moving", False))
                    self._latest_context["is_away"] = bool(getattr(st, "is_away", False))
                except Exception:
                    pass
            self._latest_context["timestamp"] = time.time()
            return dict(self._latest_context)

    def _get_active_window_title(self) -> str:
        """Get the title of the current foreground application window."""
        title = ""
        if os.name == "nt":
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value.strip()
            except Exception:
                pass
        if not title and self.window_manager and hasattr(self.window_manager, "_all_windows"):
            try:
                wins = self.window_manager._all_windows()
                if wins:
                    title = wins[0].title
            except Exception:
                pass
        return title

    def _loop(self):
        """Continuous screen monitoring loop."""
        while self._running:
            try:
                if not self.enabled:
                    time.sleep(1.0)
                    continue

                active_title = self._get_active_window_title()
                window_changed = (active_title != self._last_window) and bool(active_title)
                time_elapsed = time.time() - self._latest_context["last_screen_scan"]

                # Scan when window switches or after scan_interval has elapsed
                if window_changed or (time_elapsed >= self.scan_interval):
                    self._last_window = active_title
                    self._scan_screen(active_title)

            except Exception as e:
                logger.debug(f"Vision daemon loop tick error: {e}")

            time.sleep(1.5)

    def _scan_screen(self, active_title: str):
        """Perform lightweight screen perception and classify activity."""
        screen_text = ""
        has_error = False
        error_detail = ""

        if self.screenshot_engine:
            try:
                sc_path = self.screenshot_engine.capture()
                if sc_path and os.path.exists(sc_path) and self.ocr_engine and self.ocr_engine.is_available():
                    ocr_res = self.ocr_engine.extract_text(sc_path)
                    screen_text = (ocr_res.get("text") if isinstance(ocr_res, dict) else str(ocr_res or ""))[:2500]
            except Exception as e:
                logger.debug(f"Screen capture OCR tick error: {e}")

        # Classify task
        combined = f"{active_title} {screen_text}".lower()

        # Error detection
        if any(w in combined for w in ("traceback", "error:", "exception:", "syntaxerror", "modulenotfounderror", "typeerror", "referenceerror", "failed")):
            has_error = True
            err_m = re.search(r"((?:[A-Za-z]+Error|Exception):\s*[^\n\r]+)", screen_text, re.IGNORECASE)
            error_detail = err_m.group(1).strip() if err_m else "error visible on screen"

        # Activity categorization
        activity = "General Work"
        clean_win = re.sub(r"[\-\–\|].*$", "", active_title).strip() or "Desktop"

        if any(w in combined for w in ("visual studio code", "vscode", "pycharm", "sublime", "notepad++", "github desktop", ".py", ".js", ".html")):
            activity = "Software Development / Coding"
            summary = f"Editing code in {clean_win}."
        elif any(w in combined for w in ("chrome", "edge", "firefox", "brave", "safari", "google")):
            activity = "Web Research & Browsing"
            summary = f"Browsing online in {clean_win}."
        elif any(w in combined for w in ("terminal", "cmd", "powershell", "bash", "zsh")):
            activity = "Command Line / Terminal Execution"
            summary = f"Executing terminal commands in {clean_win}."
        elif any(w in combined for w in ("whatsapp", "telegram", "slack", "discord", "teams")):
            activity = "Messaging & Collaboration"
            summary = f"Communicating in {clean_win}."
        elif any(w in combined for w in ("word", "excel", "powerpoint", "pdf", "acrobat", "docs", "sheets")):
            activity = "Document Processing"
            summary = f"Working on documents in {clean_win}."
        elif any(w in combined for w in ("youtube", "spotify", "netflix", "vlc")):
            activity = "Media Entertainment"
            summary = f"Playing media in {clean_win}."
        else:
            activity = "System Desktop"
            summary = f"Active window: {active_title}" if active_title else "Viewing desktop."

        if has_error:
            summary += f" [Alert: {error_detail}]"

        with self._context_lock:
            self._latest_context["active_window"] = active_title
            self._latest_context["activity_type"] = activity
            self._latest_context["screen_summary"] = summary
            self._latest_context["has_error"] = has_error
            self._latest_context["error_detail"] = error_detail
            self._latest_context["last_screen_scan"] = time.time()
