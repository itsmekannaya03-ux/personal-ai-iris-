"""
Autonomous Screen Perception & Silent Work Assistant for IRIS.
When the user is looking at their PC and silent (not responding to voice),
IRIS automatically scans the active window and screen via OCR and vision
to understand what the user is working on and offers contextual assistance.
"""

import os
import re
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("iris.vision.screen_assistant")


class ScreenAssistant:
    """Proactively assists the user by scanning active screen context during silent focus."""

    def __init__(self, cooldown_seconds: float = 180.0):
        self._cooldown = cooldown_seconds
        self._last_proactive_time: float = 0.0

    def should_trigger(self) -> bool:
        """Check if cooldown has elapsed."""
        return (time.time() - self._last_proactive_time) >= self._cooldown

    def analyze_work_and_help(self, screenshot_engine, ocr_engine, window_manager, brain=None, voice_engine=None) -> Optional[dict]:
        """
        Inspect foreground window title and screen text, infer user's active task,
        and generate proactive, empathetic assistance.
        """
        if not self.should_trigger():
            return None

        # 1. Get active foreground window title
        active_title = ""
        if window_manager and hasattr(window_manager, "_all_windows"):
            try:
                wins = window_manager._all_windows()
                if wins:
                    active_title = wins[0].title
            except Exception:
                pass

        if not active_title and os.name == "nt":
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                active_title = buf.value
            except Exception:
                pass

        # 2. Capture screenshot & OCR
        screen_text = ""
        if screenshot_engine and ocr_engine:
            try:
                sc_path = screenshot_engine.capture()
                if sc_path and os.path.exists(sc_path):
                    ocr_res = ocr_engine.extract_text(sc_path)
                    screen_text = (ocr_res.get("text") if isinstance(ocr_res, dict) else str(ocr_res or ""))[:2000]
            except Exception as e:
                logger.debug(f"Screen scan error: {e}")

        # 3. Contextual Inference
        t_low = (active_title + " " + screen_text).lower()
        offer = None

        # Check for Coding & Errors (VS Code, PyCharm, Terminal)
        if any(w in t_low for w in ("traceback", "error:", "exception:", "syntaxerror", "modulenotfounderror", "typeerror")):
            err_m = re.search(r"((?:[A-Za-z]+Error|Exception):\s*[^\n\r]+)", screen_text, re.IGNORECASE)
            err_detail = err_m.group(1).strip() if err_m else "an error on your screen"
            clean_title = re.sub(r"[\-\–\|].*$", "", active_title).strip() or "your code"
            offer = f"I see {err_detail} in {clean_title}. Would you like me to investigate and fix that for you, Commander?"

        # Check for Code Editing / Development
        elif any(w in t_low for w in ("visual studio code", "vscode", "pycharm", "sublime", "notepad++", ".py", ".js", ".jsx", ".ts", ".html")):
            clean_title = re.sub(r"[\-\–\|].*$", "", active_title).strip()
            offer = f"I see you're focused on coding in {clean_title}. Let me know if you want me to write tests, refactor, or review anything."

        # Check for Research / Documentation / Reading
        elif any(w in t_low for w in ("chrome", "edge", "firefox", "brave", "documentation", "docs", "github", "stackoverflow", "arxiv")):
            clean_title = re.sub(r"[\-\–\|].*$", "", active_title).strip()
            offer = f"Looks like you're researching {clean_title}. Would you like a quick summary of the key points or code snippets from this page?"

        # Default gentle productivity offer
        elif active_title and len(active_title) > 3:
            clean_title = re.sub(r"[\-\–\|].*$", "", active_title).strip()
            offer = f"I see you're working in {clean_title}. I'm standing by right here if you need any assistance, Commander."

        if not offer:
            return None

        self._last_proactive_time = time.time()
        logger.info(f"ScreenAssistant triggered proactive help: '{offer}'")

        # Deliver via Voice synthesizer if available
        if voice_engine and hasattr(voice_engine, "speak"):
            try:
                voice_engine.speak(offer, preset="sweet")
            except Exception:
                pass

        return {
            "success": True,
            "window": active_title,
            "offer": offer,
            "timestamp": self._last_proactive_time,
        }
